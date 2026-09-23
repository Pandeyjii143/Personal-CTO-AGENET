"""Password hashing and JWT access-token utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for persistent storage."""
    return pwd_context.hash(password)


def create_access_token(
    data: Mapping[str, Any], expires_delta: timedelta | None = None
) -> str:
    """Create a signed access token. The payload must contain a subject."""
    subject = data.get("sub")
    if subject is None or not str(subject).strip():
        raise ValueError("Access-token data must include a non-empty 'sub' claim")

    now = datetime.now(timezone.utc)
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    claims = dict(data)
    # Set security-critical claims last so callers cannot override them.
    claims.update(
        {
            "sub": str(subject),
            "iat": int(now.timestamp()),
            "exp": int((now + expires_delta).timestamp()),
            "token_type": "access",
        }
    )
    return jwt.encode(
        claims,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def verify_token(token: str) -> dict[str, Any] | None:
    """Decode and validate an access token, returning claims or ``None``."""
    try:
        claims = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject.strip():
            return None
        if claims.get("token_type") != "access":
            return None
        if not isinstance(claims.get("exp"), (int, float)):
            return None
        return claims
    except (JWTError, TypeError, ValueError):
        return None
