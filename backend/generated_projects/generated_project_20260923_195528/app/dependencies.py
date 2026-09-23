from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import Integer, inspect
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _setting(*names: str) -> Any:
    """Read a setting while supporting common uppercase and lowercase names."""
    for name in names:
        value = getattr(settings, name, None)
        if value is not None:
            return value
    raise RuntimeError(f"Missing required configuration setting: {' or '.join(names)}")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate the bearer token and load the persisted user it identifies."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        secret_key = _setting("SECRET_KEY", "secret_key")
        algorithm = _setting("ALGORITHM", "algorithm")
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject:
            raise credentials_exception
    except (JWTError, RuntimeError, TypeError, ValueError):
        raise credentials_exception

    try:
        id_column = inspect(User).columns.get("id")
        identity: Any = subject
        if id_column is not None and isinstance(id_column.type, Integer):
            identity = int(subject)
        user = db.query(User).filter(User.id == identity).first()
    except (TypeError, ValueError):
        raise credentials_exception

    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Reject accounts explicitly marked inactive; models without that field are allowed."""
    if getattr(current_user, "is_active", True) is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user
