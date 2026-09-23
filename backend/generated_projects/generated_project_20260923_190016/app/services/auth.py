from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User


_password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return whether a plaintext password matches its stored hash."""
    return _password_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password before storing it."""
    return _password_context.hash(password)


def create_access_token(
    data: dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create a signed JWT access token with an expiration claim."""
    payload = data.copy()
    expires_at = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload["exp"] = expires_at
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Decode and validate a JWT, returning None if it is invalid or expired."""
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        return None


def verify_access_token(token: str) -> Optional[str]:
    """Validate a JWT and return its subject, if present."""
    payload = decode_access_token(token)
    if payload is None:
        return None

    subject = payload.get("sub")
    return str(subject) if subject is not None else None


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Return an active user when the email and password are valid."""
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(password, user.hashed_password):
        return None
    if not getattr(user, "is_active", True):
        return None
    return user