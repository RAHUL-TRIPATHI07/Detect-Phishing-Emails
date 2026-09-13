import secrets


def generate_session_id() -> str:
    """Generate a cryptographically secure session identifier."""
    return secrets.token_urlsafe(32)