from sqlalchemy import select

from src.database import SessionLocal
from src.models import OAuthAccount
from src.security import encrypt_token, decrypt_token


def save_oauth_account(
    session_id: str,
    email_address: str,
    refresh_token: str
):
    if not session_id:
        raise ValueError("session_id is required.")

    if not email_address:
        raise ValueError("email_address is required.")

    if not refresh_token:
        raise ValueError("refresh_token is required.")

    encrypted_token = encrypt_token(refresh_token)

    with SessionLocal() as db:
        account = db.scalar(
            select(OAuthAccount).where(
                OAuthAccount.email_address == email_address
            )
        )

        if account:
            account.session_id = session_id
            account.encrypted_refresh_token = encrypted_token
        else:
            account = OAuthAccount(
                session_id=session_id,
                email_address=email_address,
                encrypted_refresh_token=encrypted_token
            )
            db.add(account)

        db.commit()
        db.refresh(account)

        return account.id


def get_oauth_account(session_id: str):
    if not session_id:
        raise ValueError("session_id is required.")

    with SessionLocal() as db:
        return db.scalar(
            select(OAuthAccount).where(
                OAuthAccount.session_id == session_id
            )
        )


def get_refresh_token(session_id: str):
    account = get_oauth_account(session_id)

    if account is None:
        return None

    return decrypt_token(
        account.encrypted_refresh_token
    )


def delete_oauth_account(session_id: str):
    if not session_id:
        raise ValueError("session_id is required.")

    with SessionLocal() as db:
        account = db.scalar(
            select(OAuthAccount).where(
                OAuthAccount.session_id == session_id
            )
        )

        if account is None:
            return False

        db.delete(account)
        db.commit()

        return True