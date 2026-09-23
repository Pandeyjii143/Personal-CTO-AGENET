from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User


_password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return a bcrypt hash for a plaintext password."""
    return _password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its stored hash."""
    try:
        return _password_context.verify(plain_password, hashed_password)
    except (TypeError, ValueError):
        return False


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[dict[str, Any]] = None,
) -> str:
    """Create a signed JWT access token for the given subject."""
    if not subject:
        raise ValueError("Token subject must not be empty")

    now = datetime.now(timezone.utc)
    lifetime = expires_delta or timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    claims: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": now + lifetime,
    }
    if extra_claims:
        # Prevent callers from replacing security-sensitive registered claims.
        claims.update(
            {
                key: value
                for key, value in extra_claims.items()
                if key not in {"sub", "iat", "exp"}
            }
        )

    return jwt.encode(claims, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate an access token, raising JWTError if invalid."""
    claims = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    if not claims.get("sub"):
        raise JWTError("Token is missing a subject")
    return claims


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Retrieve a user by email address."""
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Return the matching user when the supplied credentials are valid."""
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    if hasattr(user, "is_active") and not user.is_active:
        return None
    return user
