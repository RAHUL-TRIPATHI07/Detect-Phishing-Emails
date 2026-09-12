"""
Email preprocessing utilities.

Responsible for parsing raw email messages and extracting
the subject and meaningful body text.
"""

from email import policy
from email.parser import BytesParser

from bs4 import BeautifulSoup


# Email parser
parser = BytesParser(policy=policy.default)


def html_to_text(html):
    """
    Convert HTML content into readable plain text.
    """

    soup = BeautifulSoup(html, "html.parser")

    # Remove non-content elements
    for tag in soup(["script", "style"]):
        tag.decompose()

    return soup.get_text(
        separator=" ",
        strip=True
    )

def extract_email_content(raw_bytes):
    """
    Extract subject and meaningful body text
    from a raw email message.

    Args:
        raw_bytes (bytes): Raw .eml email content.

    Returns:
        tuple: (subject, body)
    """

    if not isinstance(raw_bytes, bytes):
        raise TypeError("raw_bytes must be bytes.")

    msg = parser.parsebytes(raw_bytes)

    # Extract subject
    subject = msg.get("Subject", "")

    if subject is None:
        subject = ""

    subject = str(subject).strip()

    plain_parts = []
    html_parts = []

    if msg.is_multipart():

        for part in msg.walk():

            if part.is_multipart():
                continue

            # Ignore attachments
            if part.get_content_disposition() == "attachment":
                continue

            content_type = part.get_content_type()

            try:
                content = part.get_content()
            except Exception:
                continue

            if not isinstance(content, str):
                continue

            if content_type == "text/plain":
                plain_parts.append(content)

            elif content_type == "text/html":
                html_parts.append(
                    html_to_text(content)
                )

    else:

        content_type = msg.get_content_type()

        try:
            content = msg.get_content()
        except Exception:
            content = ""

        if isinstance(content, str):

            if content_type == "text/plain":
                plain_parts.append(content)

            elif content_type == "text/html":
                html_parts.append(
                    html_to_text(content)
                )

    # Prefer plain text when available
    if plain_parts:
        body = "\n".join(plain_parts)
    else:
        body = "\n".join(html_parts)

    body = body.strip()

    return subject, body

def validate_email_content(raw_bytes):
    """
    Validate whether raw bytes contain a usable email message.

    Args:
        raw_bytes (bytes): Raw email content.

    Returns:
        bool: True if the content appears to be a valid email.
    """

    if not isinstance(raw_bytes, bytes):
        raise TypeError("raw_bytes must be bytes.")

    msg = parser.parsebytes(raw_bytes)

    has_email_header = any(
        msg.get(header)
        for header in ["From", "To", "Subject", "Date"]
    )

    subject, body = extract_email_content(raw_bytes)

    has_content = bool(subject.strip() or body.strip())

    return has_email_header and has_content

