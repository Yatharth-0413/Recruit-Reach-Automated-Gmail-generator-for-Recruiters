
import os
import base64
import mimetypes

from email.message import EmailMessage
from datetime import datetime

from gmail.auth import get_gmail_service
from database import Application, SessionLocal


def send_application_email(
    to_email,
    recruiter_name,
    company,
    role,
    resume_path,
    subject_template,
    body_template
):
    if not os.path.isfile(resume_path):
        raise FileNotFoundError(resume_path)

    # Prevent duplicate applications to the same role
    db = SessionLocal()

    try:
        existing = db.query(Application).filter(
            Application.recruiter_email == to_email,
            Application.role == role
        ).first()

        if existing:
            raise ValueError(
                f"Already applied to {company} for {role}"
            )
    finally:
        db.close()

    # Personalize email
    values = {
        "recruiter_name": recruiter_name,
        "company": company,
        "role": role
    }

    subject = subject_template.format(**values)
    body = body_template.format(**values)

    message = EmailMessage()
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    # Attach resume
    mime_type, _ = mimetypes.guess_type(resume_path)

    if mime_type is None:
        mime_type = "application/pdf"

    maintype, subtype = mime_type.split("/", 1)

    with open(resume_path, "rb") as file:
        message.add_attachment(
            file.read(),
            maintype=maintype,
            subtype=subtype,
            filename=os.path.basename(resume_path)
        )

    encoded = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    service = get_gmail_service()

    result = service.users().messages().send(
        userId="me",
        body={"raw": encoded}
    ).execute()

    # Save application
    db = SessionLocal()

    try:
        application = Application(
            company=company,
            recruiter_name=recruiter_name,
            recruiter_email=to_email,
            role=role,
            subject=subject,
            thread_id=result["threadId"],
            status="Sent",
            sent_at=datetime.now()
        )

        db.add(application)
        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

    return result
