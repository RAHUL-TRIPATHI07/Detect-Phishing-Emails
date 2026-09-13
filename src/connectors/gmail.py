"""
Gmail connector.

Handles Gmail OAuth authentication and message retrieval.
"""

import base64

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


from src.config import (
    GMAIL_REDIRECT_URI,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
)

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]


REDIRECT_URI = GMAIL_REDIRECT_URI


def create_gmail_flow():
    """
    Create a Google OAuth flow for Gmail access.
    """

    if not GOOGLE_CLIENT_ID:
        raise ValueError(
            "Google OAuth client ID is not configured."
        )

    if not GOOGLE_CLIENT_SECRET:
        raise ValueError(
            "Google OAuth client secret is not configured."
        )

    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=GMAIL_SCOPES,
        autogenerate_code_verifier=False
    )

    flow.redirect_uri = GMAIL_REDIRECT_URI

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
        credentials=credentials,
        cache_discovery=False
    )

    return service

def get_gmail_account_email(credentials):
    """
    Retrieve the email address of the authenticated Gmail account.
    """

    service = create_gmail_service(credentials)

    profile = (
        service.users()
        .getProfile(userId="me")
        .execute()
    )

    email_address = profile["emailAddress"]

    if not email_address:
        raise ValueError(
            "Unable to determine the Gmail account email address."
        )

    return email_address


def list_gmail_messages(credentials, limit=20, page_token=None):
    """
    List Gmail messages with pagination support.

    Args:
        credentials: Google OAuth credentials.
        limit: Maximum number of messages to retrieve.
        page_token: Gmail pagination token for the next page.

    Returns:
        Dictionary containing:
            - messages
            - next_page_token
    """

    if not isinstance(limit, int):
        raise TypeError("limit must be an integer.")

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    if page_token is not None and not isinstance(page_token, str):
        raise TypeError("page_token must be a string or None.")

    service = create_gmail_service(credentials)

    request_kwargs = {
        "userId": "me",
        "maxResults": limit
    }

    if page_token:
        request_kwargs["pageToken"] = page_token

    response = (
        service.users()
        .messages()
        .list(**request_kwargs)
        .execute()
    )
    
    return {
        "messages": response.get("messages", []),
         "next_page_token": response.get("nextPageToken")
    }
       

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


def get_gmail_credentials(refresh_token):
    """
    Create Gmail credentials from a stored refresh token.
    """

    if not isinstance(refresh_token, str) or not refresh_token.strip():
        raise ValueError(
            "OAuth refresh token is missing."
        )

    flow = create_gmail_flow()

    client_config = flow.client_config
   
    # Google OAuth client configuration may be wrapped
    # under "web" or "installed".
    if "web" in client_config:
        client_config = client_config["web"]
    elif "installed" in client_config:
        client_config = client_config["installed"]

    client_id = client_config.get("client_id")
    client_secret = client_config.get("client_secret")

    if not client_id:
        raise ValueError(
            "Google OAuth client ID is missing."
        )

    if not client_secret:
        raise ValueError(
            "Google OAuth client secret is missing."
        )

    return Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=GMAIL_SCOPES
    )

def scan_gmail_messages(credentials, limit=20, page_token=None):
    """
    Retrieve Gmail messages with metadata and raw email content.

    Args:
        credentials: Google OAuth credentials.
        limit: Maximum number of messages to retrieve.

    Returns:
        List of dictionaries containing Gmail metadata and raw bytes.
    """

    page = list_gmail_messages(
    credentials=credentials,
    limit=limit,
    page_token=page_token
)

    messages = page["messages"]
    next_page_token = page["next_page_token"]

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
        
            
            payload = gmail_message.get("payload", {})

            headers = {
                header["name"].lower(): header["value"]
                for header in payload.get("headers", [])
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

    return {
      "results": results,
      "next_page_token": next_page_token
    }