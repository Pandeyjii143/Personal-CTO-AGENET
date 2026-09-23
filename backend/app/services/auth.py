from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User


_password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    """Hash a plaintext password for safe storage."""
    return _password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compare a plaintext password with its stored hash."""
    return _password_context.verify(plain_password, hashed_password)


def get_user_by_email(db: Session, email: str) -> User | None:
    normalized_email = email.strip().lower()
    return db.query(User).filter(User.email == normalized_email).first()


def create_user(db: Session, email: str, password: str) -> User:
    """Create and persist a user, rejecting duplicate email addresses."""
    normalized_email = email.strip().lower()
    if get_user_by_email(db, normalized_email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(email=normalized_email, hashed_password=hash_password(password))
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        ) from exc
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Return the matching user when the supplied credentials are valid."""
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """Create a signed JWT access token."""
    payload = data.copy()
    now = datetime.now(timezone.utc)
    lifetime = expires_delta or timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload.update({"iat": now, "exp": now + lifetime})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Validate an access token and return its persisted user."""
    unauthorized = HTTPException(
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
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject:
            raise unauthorized
    except JWTError as exc:
        raise unauthorized from exc

    user = db.query(User).filter(User.id == subject).first()
    if user is None:
        raise unauthorized
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require the authenticated account to be active."""
    if not getattr(current_user, "is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user
