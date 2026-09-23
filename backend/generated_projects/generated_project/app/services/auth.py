from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plaintext password against its stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for secure persistence."""
    return pwd_context.hash(password)


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Return the matching active user, or None when credentials are invalid."""
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        return None

    stored_hash = getattr(user, "hashed_password", None) or getattr(
        user, "password_hash", None
    )
    if not stored_hash or not verify_password(password, stored_hash):
        return None
    if not getattr(user, "is_active", True):
        return None
    return user


def create_access_token(
    data: dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create a signed JWT, adding an expiry and requiring a subject claim."""
    claims = data.copy()
    subject = claims.get("sub")
    if subject is None:
        raise ValueError("Access-token data must include a 'sub' claim")

    if expires_delta is None:
        expires_delta = timedelta(
            minutes=getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 30)
        )

    now = datetime.now(timezone.utc)
    claims["iat"] = now
    claims["exp"] = now + expires_delta
    return jwt.encode(
        claims,
        settings.SECRET_KEY,
        algorithm=getattr(settings, "ALGORITHM", "HS256"),
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT, raising ValueError for invalid tokens."""
    try:
        claims = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[getattr(settings, "ALGORITHM", "HS256")],
        )
    except JWTError as exc:
        raise ValueError("Invalid or expired access token") from exc

    if not claims.get("sub"):
        raise ValueError("Access token is missing its subject")
    return claims


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Resolve the authenticated token subject to an active persisted user."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        claims = decode_access_token(token)
        subject = str(claims["sub"])
    except (ValueError, KeyError):
        raise unauthorized

    user = db.query(User).filter(User.email == subject).first()
    if user is None:
        # Tokens may use a database ID as their subject instead of an email.
        user_id = getattr(User, "id", None)
        if user_id is not None:
            user = db.query(User).filter(user_id == subject).first()

    if user is None or not getattr(user, "is_active", True):
        raise unauthorized
    return user
