
from gmail.auth import get_gmail_service


def test_connection():

    service = get_gmail_service()

    profile = service.users().getProfile(
        userId="me"
    ).execute()

    print("\nGmail connected successfully!")
    print("Email:", profile["emailAddress"])
    print("Total messages:", profile["messagesTotal"])


if __name__ == "__main__":
    test_connection()
