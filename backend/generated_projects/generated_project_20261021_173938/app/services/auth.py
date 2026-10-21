from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.user import User


class AuthenticationError(ValueError):
    """Raised when credentials or a refresh token are invalid."""


def _create_token(subject: Any, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_token_pair(user: User) -> dict[str, str]:
    """Create an access and refresh token pair for a user."""
    access_token = _create_token(
        user.id,
        "access",
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = _create_token(
        user.id,
        "refresh",
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    """Return the matching active user, or None when credentials are invalid."""
    normalized_email = email.strip().lower()
    result = await db.execute(select(User).where(User.email == normalized_email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


async def register_user(db: AsyncSession, email: str, password: str) -> User:
    """Create and persist a user with a securely hashed password."""
    normalized_email = email.strip().lower()
    if not normalized_email or not password:
        raise ValueError("Email and password are required")

    result = await db.execute(select(User).where(User.email == normalized_email))
    if result.scalar_one_or_none() is not None:
        raise ValueError("A user with this email already exists")

    user = User(
        email=normalized_email,
        hashed_password=get_password_hash(password),
        is_active=True,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ValueError("A user with this email already exists") from exc

    await db.refresh(user)
    return user


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> dict[str, str]:
    """Validate a refresh token and issue a new token pair."""
    try:
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError as exc:
        raise AuthenticationError("Invalid or expired refresh token") from exc

    subject = payload.get("sub")
    if not subject or payload.get("type") != "refresh":
        raise AuthenticationError("Invalid refresh token")

    result = await db.execute(select(User).where(User.id == subject))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise AuthenticationError("User is unavailable")

    return create_token_pair(user)
