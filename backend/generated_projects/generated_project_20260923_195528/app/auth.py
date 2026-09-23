import os
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _secret_key() -> str:
    secret = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET_KEY")
    if not secret:
        raise RuntimeError("Set SECRET_KEY or JWT_SECRET_KEY in the environment")
    return secret


def _algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", "HS256")


def _access_token_expire_minutes() -> int:
    try:
        minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    except ValueError as exc:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be an integer") from exc
    if minutes <= 0:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be greater than zero")
    return minutes


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its stored password hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password before persisting it; never store plain-text passwords."""
    return pwd_context.hash(password)


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Return the matching user when the supplied credentials are valid."""
    normalized_email = email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed access token with a subject and UTC expiration."""
    now = datetime.now(timezone.utc)
    expires_at = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=_access_token_expire_minutes())
    )
    payload: dict[str, Any] = dict(claims or {})
    payload.update({"sub": str(subject), "iat": now, "exp": expires_at, "type": "access"})
    return jwt.encode(payload, _secret_key(), algorithm=_algorithm())


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decode and validate an access token, then load its persisted user."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, _secret_key(), algorithms=[_algorithm()])
        subject = payload.get("sub")
        if not subject or payload.get("type") != "access":
            raise credentials_error
    except (JWTError, RuntimeError, ValueError) as exc:
        raise credentials_error from exc

    user = db.query(User).filter(User.id == subject).first()
    if user is None:
        raise credentials_error
    return user


def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    """Reject authenticated users whose account has been disabled."""
    if not getattr(user, "is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return user
