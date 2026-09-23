from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


_password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compare a plain-text password with its stored hash."""
    try:
        return _password_context.verify(plain_password, hashed_password)
    except (TypeError, ValueError):
        return False


def get_password_hash(password: str) -> str:
    """Return a secure hash for a plain-text password."""
    return _password_context.hash(password)


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """Create a signed JWT access token. The payload must contain a subject (`sub`)."""
    subject = data.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("Access-token data must include a non-empty string 'sub'.")

    now = datetime.now(timezone.utc)
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = dict(data)
    payload["iat"] = now
    payload["exp"] = now + expires_delta

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate an access token, raising JWTError if it is invalid."""
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        raise JWTError("Token is missing a valid subject.")
    return payload
