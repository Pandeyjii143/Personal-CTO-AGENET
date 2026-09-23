import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["authentication"])

# Configure JWT_SECRET_KEY (or SECRET_KEY) in the application environment.
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)
    password: str = Field(..., min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: Any
    email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


def _secret_key() -> str:
    secret = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")
    if not secret or len(secret) < 32:
        raise RuntimeError(
            "Set JWT_SECRET_KEY (or SECRET_KEY) to a random value of at least 32 characters."
        )
    return secret


def _normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A valid email address is required.",
        )
    return normalized


def _create_access_token(user_id: Any) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    claims = {
        "sub": str(user_id),
        "type": "access",
        "iat": datetime.now(timezone.utc),
        "exp": expires_at,
    }
    return jwt.encode(claims, _secret_key(), algorithm=JWT_ALGORITHM)


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return _pwd_context.verify(plain_password, hashed_password)
    except (TypeError, ValueError):
        return False


def _hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def get_current_user(
    token: str = Depends(_oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, _secret_key(), algorithms=[JWT_ALGORITHM])
        subject = payload.get("sub")
        if not subject or payload.get("type") != "access":
            raise credentials_error
    except (JWTError, RuntimeError):
        raise credentials_error

    user = db.query(User).filter(User.id == subject).first()
    if user is None:
        # Support integer primary keys while keeping the JWT subject a string.
        try:
            user = db.query(User).filter(User.id == int(subject)).first()
        except (TypeError, ValueError):
            user = None
    if user is None or not getattr(user, "is_active", True):
        raise credentials_error
    return user


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    email = _normalize_email(payload.email)
    if db.query(User).filter(User.email == email).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(email=email, hashed_password=_hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = _normalize_email(payload.email)
    user = db.query(User).filter(User.email == email).first()
    if (
        user is None
        or not _verify_password(payload.password, user.hashed_password)
        or not getattr(user, "is_active", True)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=_create_access_token(user.id),
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user
