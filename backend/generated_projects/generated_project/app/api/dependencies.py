from typing import Any

from fastapi import Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(__import__("fastapi.security", fromlist=["OAuth2PasswordBearer"]).OAuth2PasswordBearer(
        tokenUrl="/api/v1/auth/login"
    )),
    db: Session = Depends(get_db),
) -> User:
    """Decode the bearer token and return the user identified by its ``sub`` claim.

    ``decode_access_token`` is expected to return the decoded claims, or ``None``
    when the token is invalid. The token subject is the user's database ID.
    """
    try:
        payload: Any = decode_access_token(token)
    except (JWTError, ValueError, TypeError):
        raise _unauthorized() from None

    if not isinstance(payload, dict):
        raise _unauthorized()

    subject = payload.get("sub")
    if subject is None:
        raise _unauthorized()

    user = db.query(User).filter(User.id == subject).first()
    if user is None:
        raise _unauthorized()

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Return the authenticated user only if the account is active."""
    if not getattr(current_user, "is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user
