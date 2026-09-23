from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from jose import JWTError, jwt

from app.core.config import settings


def create_access_token(
    data: Mapping[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token from the supplied claims."""
    now = datetime.now(timezone.utc)
    expires_at = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    if expires_at <= now:
        raise ValueError("Token expiration must be in the future")

    claims = dict(data)
    claims["iat"] = now
    claims["exp"] = expires_at

    return jwt.encode(
        claims,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate an access token, raising JWTError if invalid."""
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    if not isinstance(payload, dict):
        raise JWTError("Invalid token payload")
    return payload
