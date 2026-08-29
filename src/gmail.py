import base64
import os
import json
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# ============================================================
# CONFIGURATION
# ============================================================

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]

FROM_EMAIL = "shameemkpofficial@gmail.com"
TO_EMAIL = "shameemkppersonal@gmail.com"


# ============================================================
# GMAIL AUTHENTICATION
# ============================================================

def get_gmail_service():
    credentials = None

    # GitHub Actions
    token_json = os.getenv("GMAIL_TOKEN_JSON")

    if token_json:
        credentials = Credentials.from_authorized_user_info(
            json.loads(token_json),
            SCOPES,
        )

    # Local development
    elif os.path.exists(TOKEN_FILE):
        credentials = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES,
        )

    if not credentials:
        raise RuntimeError(
            "Gmail credentials are not available."
        )

    if not credentials.valid:

        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        else:
            raise RuntimeError(
                "Gmail authorization expired. "
                "Run the local OAuth authorization again."
            )

    return build(
        "gmail",
        "v1",
        credentials=credentials,
    )

# ============================================================
# SEND EMAIL
# ============================================================

def send_email(
    service,
    to_email,
    subject,
    body,
):

    message = EmailMessage()

    message["From"] = FROM_EMAIL
    message["To"] = to_email
    message["Subject"] = subject

    message.set_content(body)

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    result = service.users().messages().send(
        userId="me",
        body={
            "raw": encoded_message,
        },
    ).execute()

    return result


# ============================================================
# TEST
# ============================================================

def main():

    print("Connecting to Gmail...")

    service = get_gmail_service()

    print("Gmail authentication successful.")

    print(
        f"Sending test email to {TO_EMAIL}..."
    )

    result = send_email(
        service=service,
        to_email=TO_EMAIL,
        subject="Abu Dhabi Lead Finder - Gmail Test",
        body=(
            "Hello Shameem,\n\n"
            "This is a test email from the "
            "Abu Dhabi Lead Finder automation.\n\n"
            "Gmail API integration is working successfully.\n\n"
            "Regards,\n"
            "Abu Dhabi Lead Finder"
        ),
    )

    print(
        "Email sent successfully."
    )

    print(
        f"Message ID: {result.get('id')}"
    )


if __name__ == "__main__":
    main()