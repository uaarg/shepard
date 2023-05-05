from __future__ import print_function

import os.path

import base64
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]


def create_draft_email(service, message_text):
    try:
        message = EmailMessage()
        message.set_content(message_text)
        message["To"] = "umtariq@ualberta.ca"
        message["From"] = "dev.uaarg@gmail.com"
        message["Subject"] = "Email API Test"

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"message": {"raw": encoded_message}}

        draft = (
            service.users().drafts().create(userId="me", body=create_message).execute()
        )

        print(f'Draft id: {draft["id"]}\nDraft message: {draft["message"]}')
    except HttpError as error:
        print(f"HTTP Error occurred: {error}")
        exit(2)

    return draft


def verify_email():
    pass


def send_email():
    pass


def main():
    """
    # TODO: ADD DOCSTRING
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)

        # TODO: Compose a draft email, verify with user, send email.
        message_text = "This is text for a test message."
        create_draft_email(service, message_text)

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")
        exit(1)


if __name__ == "__main__":
    main()
