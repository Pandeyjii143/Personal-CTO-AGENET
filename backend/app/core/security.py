from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


_password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its stored hash."""
    return _password_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storage; never persist plaintext passwords."""
    return _password_context.hash(password)


def create_access_token(
    data: Mapping[str, Any], expires_delta: timedelta | None = None
) -> str:
    """Create a signed JWT access token from the supplied claims."""
    claims = dict(data)
    expires_in = expires_delta or timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    now = datetime.now(timezone.utc)
    claims.update(
        {
            "iat": now,
            "exp": now + expires_in,
            "token_type": "access",
        }
    )
    return jwt.encode(claims, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT, raising JWTError for invalid tokens."""
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        options={"require_exp": True, "require_sub": True},
    )


def verify_token(
    token: str,
    credentials_exception: HTTPException | None = None,
) -> dict[str, Any]:
    """Validate an access token and return its claims."""
    if credentials_exception is None:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(token)
        if payload.get("token_type") != "access":
            raise credentials_exception
        return payload
    except (JWTError, TypeError, ValueError):
        raise credentials_exception
