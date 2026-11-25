from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone

import jwt

from .auth_config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Hash the user's password before storing it.
    """
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    """
    Verify the entered password against the stored hash.
    """
    return password_hash.verify(
        plain_password,
        hashed_password
    )



def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expire
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token