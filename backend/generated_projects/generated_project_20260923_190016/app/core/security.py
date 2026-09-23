from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


_password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return whether a plain-text password matches its stored hash."""
    return _password_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for secure storage."""
    return _password_context.hash(password)


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """Create a signed JWT access token containing the supplied claims."""
    now = datetime.now(timezone.utc)
    expires_at = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    claims = data.copy()
    claims.update({"iat": now, "exp": expires_at, "type": "access"})
    return jwt.encode(claims, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Validate and decode an access token, returning None if it is invalid."""
    try:
        claims = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        return None

    if claims.get("type") != "access":
        return None
    return claims
