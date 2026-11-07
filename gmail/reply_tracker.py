import base64
import re
import html

from datetime import datetime, timezone
from email.utils import parseaddr

from gmail.auth import get_gmail_service
from database import Application, SessionLocal
from gmail.reply_classifier import classify_reply


def get_header(headers, name):

    for header in headers or []:

        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")

    return ""


def get_sender_address(headers):

    sender = get_header(headers, "From")

    return parseaddr(sender)[1].lower()


def decode_body(data):

    if not data:
        return ""

    try:

        padding = "=" * (-len(data) % 4)

        decoded = base64.urlsafe_b64decode(
            data + padding
        )

        return decoded.decode(
            "utf-8",
            errors="replace"
        )

    except Exception:

        return ""


def extract_message_body(payload):

    mime_type = payload.get("mimeType", "")
    body = payload.get("body", {})

    if mime_type == "text/plain":

        return decode_body(
            body.get("data", "")
        )

    parts = payload.get("parts", [])

    # Prefer plain-text content
    for part in parts:

        result = extract_message_body(part)

        if result:
            return result

    # HTML fallback
    if mime_type == "text/html":

        raw_html = decode_body(
            body.get("data", "")
        )

        clean_text = re.sub(
            r"<[^>]+>",
            " ",
            raw_html
        )

        return html.unescape(clean_text).strip()

    if not parts and body.get("data"):

        return decode_body(body["data"])

    return ""


def gmail_timestamp(message):

    milliseconds = int(message["internalDate"])

    return datetime.fromtimestamp(
        milliseconds / 1000,
        tz=timezone.utc
    ).replace(tzinfo=None)


def sync_replies():

    service = get_gmail_service()

    profile = service.users().getProfile(
        userId="me"
    ).execute()

    own_email = profile["emailAddress"].lower()

    db = SessionLocal()

    stats = {
        "checked": 0,
        "new_replies": 0,
        "applications_replied": 0,
        "errors": 0
    }

    try:

        applications = db.query(Application).filter(
            Application.thread_id.isnot(None)
        ).all()

        for application in applications:

            stats["checked"] += 1

            try:

                thread = service.users().threads().get(
                    userId="me",
                    id=application.thread_id,
                    format="full"
                ).execute()

                messages = thread.get("messages", [])

                sent_messages = []

                # Find original outgoing application email
                for message in messages:

                    payload = message.get("payload", {})

                    headers = payload.get("headers", [])

                    sender = get_sender_address(headers)

                    if sender == own_email:

                        sent_messages.append(
                            gmail_timestamp(message)
                        )

                if not sent_messages:

                    continue

                # Use Gmail's actual sent timestamp
                original_sent_at = min(sent_messages)

                application.sent_at = original_sent_at

                incoming_messages = []

                for message in messages:

                    payload = message.get("payload", {})

                    headers = payload.get("headers", [])

                    sender = get_sender_address(headers)

                    # Ignore our own messages
                    if sender == own_email:
                        continue

                    received_at = gmail_timestamp(message)

                    # Ignore messages before or at original send time
                    if received_at <= original_sent_at:
                        continue

                    incoming_messages.append({

                        "sender": get_header(
                            headers,
                            "From"
                        ),

                        "date": received_at,

                        "body": extract_message_body(payload)

                    })

                incoming_messages.sort(
                    key=lambda item: item["date"]
                )

                old_count = application.reply_count or 0

                new_count = len(incoming_messages)

                if new_count > 0:

                    first_reply = incoming_messages[0]

                    latest_reply = incoming_messages[-1]

                    application.reply_count = new_count

                    application.replied_at = (
                        first_reply["date"]
                    )

                    application.reply_content = (
                        first_reply["body"]
                    )

                    application.last_reply_at = (
                        latest_reply["date"]
                    )

                    application.last_reply_content = (
                        latest_reply["body"]
                    )

                    application.last_reply_from = (
                        latest_reply["sender"]
                    )

                    # Classify the latest incoming recruiter message.
                    # Promote the application to Interview when the reply
                    # indicates an interview, including already-Replied rows.
                    application.reply_category = classify_reply(
                        latest_reply["body"]
                    )

                    if (
                        application.reply_category == "Interview"
                        and application.status in ["Sent", "Pending", "Replied"]
                    ):
                        application.status = "Interview"
                    elif application.status in ["Sent", "Pending"]:
                        application.status = "Replied"

                    stats["applications_replied"] += 1

                    if new_count > old_count:

                        stats["new_replies"] += (
                            new_count - old_count
                        )


            except Exception as error:

                stats["errors"] += 1

                print(
                    f"Error checking {application.company}: "
                    f"{error}"
                )

        db.commit()

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()

    return stats
