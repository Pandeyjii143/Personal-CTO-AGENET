from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# bcrypt is intentionally used through Passlib so its parameters and migration
# behavior remain centralized.
_password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hash a plaintext password for persistent storage."""
    return _password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return whether a plaintext password matches its stored hash."""
    return _password_context.verify(plain_password, hashed_password)


# Descriptive aliases for callers that use these names.
hash_password = get_password_hash


def create_access_token(
    data: Mapping[str, Any], expires_delta: timedelta | None = None
) -> str:
    """Create a signed JWT access token from the supplied claims."""
    claims = dict(data)
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    claims["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(claims, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate an access token, raising 401 for invalid claims."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError as exc:
        raise credentials_exception from exc

    # Require a subject so a validly signed token cannot identify no user.
    if not payload.get("sub"):
        raise credentials_exception

    return payload


def verify_token(token: str) -> str:
    """Validate an access token and return its subject claim."""
    return str(decode_access_token(token)["sub"])
