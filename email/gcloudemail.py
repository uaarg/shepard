from __future__ import print_function

import os.path
import sys

import base64
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]


def get_parameters():
    if len(sys.argv) != 4:
        print(
            "USAGE: python gcloudemail.py <message.txt> <receiver@email.com> <subject>"
        )
        exit(3)

    with open(sys.argv[1], "r") as message_file:
        message_text = message_file.read()

    to_address = sys.argv[2]

    email_subject = sys.argv[3]

    return message_text, to_address, email_subject


def send_email(service, message_text, to_address, email_subject):
    try:
        message = EmailMessage()
        message.set_content(message_text)
        message["To"] = to_address
        message["From"] = "dev.uaarg@gmail.com"
        message["Subject"] = email_subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"raw": encoded_message}

        sent_message = (
            service.users().messages().send(userId="me", body=create_message).execute()
        )

        print(f'Message Id: {sent_message["id"]}')
    except HttpError as error:
        print(f"HTTP Error occurred: {error}")
        exit(2)

    return sent_message


def verify_details_and_send_email(service, message_text, to_address, email_subject):
    print("VERIFY EMAIL TO BE SENT")

    print("=======================")
    print(f"TO: \t\t{to_address}")
    print(f"FROM: \t\tdev.uaarg@gmail.com")
    print(f"SUBJECT: \t{email_subject}")
    print(f"MESSAGE: \n---\n{message_text}\n---")
    print("=======================")

    confirmation = input("Are these details correct (yes/no)? ")
    if confirmation.lower() == "yes":
        print(f"Sending email...")
        send_email(service, message_text, to_address, email_subject)
        print(f"Email sent successfully.")
    else:
        print(f"Email cancelled.")
        exit()


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
        message_text, to_address, email_subject = get_parameters()
        verify_details_and_send_email(service, message_text, to_address, email_subject)

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")
        exit(1)


if __name__ == "__main__":
    main()
