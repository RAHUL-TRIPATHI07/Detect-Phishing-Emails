from cryptography.fernet import Fernet

from src.config import TOKEN_ENCRYPTION_KEY


def get_fernet():
    if not TOKEN_ENCRYPTION_KEY:
        raise ValueError(
            "TOKEN_ENCRYPTION_KEY is not configured."
        )

    try:
        return Fernet(TOKEN_ENCRYPTION_KEY.encode())
    except Exception as exc:
        raise ValueError(
            "TOKEN_ENCRYPTION_KEY is invalid."
        ) from exc


def encrypt_token(token: str) -> str:
    if not isinstance(token, str) or not token:
        raise ValueError(
            "Token must be a non-empty string."
        )

    fernet = get_fernet()

    return fernet.encrypt(
        token.encode()
    ).decode()


def decrypt_token(encrypted_token: str) -> str:
    if not isinstance(encrypted_token, str) or not encrypted_token:
        raise ValueError(
            "Encrypted token must be a non-empty string."
        )

    fernet = get_fernet()

    try:
        return fernet.decrypt(
            encrypted_token.encode()
        ).decode()
    except Exception as exc:
        raise ValueError(
            "Unable to decrypt token."
        ) from exc