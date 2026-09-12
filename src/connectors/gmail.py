"""
Gmail connector.

Handles Gmail OAuth authentication and message retrieval.
"""

from pathlib import Path
import base64

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CREDENTIALS_FILE = PROJECT_ROOT / "secrets" / "credentials.json"

REDIRECT_URI = "http://127.0.0.1:8000/auth/gmail/callback"


def create_gmail_flow():
    """
    Create a Google OAuth flow for Gmail access.
    """

    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"Gmail OAuth credentials not found: {CREDENTIALS_FILE}"
        )

    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=GMAIL_SCOPES,
        autogenerate_code_verifier=False
    )

    flow.redirect_uri = REDIRECT_URI

    return flow


def create_gmail_service(credentials):
    """
    Create an authenticated Gmail API service.

    Args:
        credentials: Google OAuth credentials.

    Returns:
        Gmail API service object.
    """

    if credentials is None:
        raise ValueError("Gmail credentials are required.")

    service = build(
        "gmail",
        "v1",
        credentials=credentials
    )

    return service


def list_gmail_messages(credentials, limit=20):
    """
    List recent Gmail messages.

    Args:
        credentials: Google OAuth credentials.
        limit: Maximum number of messages to retrieve.

    Returns:
        List of Gmail message metadata.
    """

    if not isinstance(limit, int):
        raise TypeError("limit must be an integer.")

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    service = create_gmail_service(credentials)

    response = (
        service.users()
        .messages()
        .list(
            userId="me",
            maxResults=limit
        )
        .execute()
    )

    return response.get("messages", [])


def get_gmail_message_raw(credentials, message_id):
    """
    Retrieve one Gmail message in raw MIME format.

    Args:
        credentials: Google OAuth credentials.
        message_id: Gmail message ID.

    Returns:
        Raw email bytes.
    """

    if not isinstance(message_id, str) or not message_id.strip():
        raise ValueError("message_id must be a non-empty string.")

    service = create_gmail_service(credentials)

    message = (
        service.users()
        .messages()
        .get(
            userId="me",
            id=message_id,
            format="raw"
        )
        .execute()
    )

    raw_data = message.get("raw")

    if not raw_data:
        raise ValueError(
            f"Gmail message {message_id} does not contain raw data."
        )

    return base64.urlsafe_b64decode(raw_data)


def get_gmail_credentials(token_data):
    """
    Reconstruct Google OAuth credentials from stored token data.

    Args:
        token_data: Dictionary containing OAuth credential information.

    Returns:
        google.oauth2.credentials.Credentials
    """

    if not isinstance(token_data, dict):
        raise TypeError("token_data must be a dictionary.")

    token = token_data.get("token")
    refresh_token = token_data.get("refresh_token")
    token_uri = token_data.get("token_uri")
    scopes = token_data.get("scopes")

    if not token:
        raise ValueError("OAuth access token is missing.")

    flow = create_gmail_flow()

    client_config = flow.client_config

    client_id = client_config["client_id"]
    client_secret = client_config["client_secret"]

    return Credentials(
        token=token,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes
    )

def scan_gmail_messages(credentials, limit=20):
    """
    Retrieve Gmail messages with metadata and raw email content.

    Args:
        credentials: Google OAuth credentials.
        limit: Maximum number of messages to retrieve.

    Returns:
        List of dictionaries containing Gmail metadata and raw bytes.
    """

    messages = list_gmail_messages(
        credentials=credentials,
        limit=limit
    )

    service = create_gmail_service(credentials)

    results = []

    for message in messages:
        message_id = message["id"]

        try:
            gmail_message = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=message_id,
                    format="metadata",
                    metadataHeaders=[
                        "Subject",
                        "From",
                        "Date"
                    ]
                )
                .execute()
            )

            headers = {
                header["name"].lower(): header["value"]
                for header in gmail_message
                .get("payload", {})
                .get("headers", [])
            }

            raw_bytes = get_gmail_message_raw(
                credentials=credentials,
                message_id=message_id
            )

            results.append({
                "message_id": message_id,
                "thread_id": message.get("threadId"),
                "subject": headers.get("subject", ""),
                "sender": headers.get("from", ""),
                "date": headers.get("date", ""),
                "raw_bytes": raw_bytes
            })

        except Exception as exc:
            results.append({
                "message_id": message_id,
                "thread_id": message.get("threadId"),
                "raw_bytes": None,
                "error": str(exc)
            })

    return results