from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _find_user(db: Session, subject: Any) -> User | None:
    if subject is None:
        return None

    # Tokens may identify users by database ID or by email/username.
    id_column = getattr(User, "id", None)
    if id_column is not None:
        identifier = subject
        if isinstance(subject, str) and subject.isdecimal():
            identifier = int(subject)
        try:
            user = db.query(User).filter(id_column == identifier).first()
            if user is not None:
                return user
        except (TypeError, ValueError):
            pass

    for field_name in ("email", "username"):
        column = getattr(User, field_name, None)
        if column is not None:
            user = db.query(User).filter(column == subject).first()
            if user is not None:
                return user

    return None


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(token)
    except (JWTError, TypeError, ValueError):
        raise _unauthorized()

    if not isinstance(payload, dict):
        raise _unauthorized()

    user = _find_user(db, payload.get("sub"))
    if user is None:
        raise _unauthorized()

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    is_active = getattr(current_user, "is_active", getattr(current_user, "active", True))
    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user
