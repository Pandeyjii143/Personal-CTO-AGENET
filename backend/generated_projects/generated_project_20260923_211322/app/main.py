import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from contextlib import asynccontextmanager
from typing import Generator, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, create_engine, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, declarative_base, sessionmaker


# Configure JWT_SECRET_KEY with a stable, randomly generated secret in production.
# The fallback keeps local development convenient, but changes on every restart.
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or secrets.token_urlsafe(48)
JWT_ISSUER = os.getenv("JWT_ISSUER", "fastapi-auth")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

_engine_options = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    _engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(320), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=1024)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=320, description="Username or email")
    password: str = Field(min_length=1, max_length=1024)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: int
    username: str
    email: str


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32
    )
    return f"scrypt${_b64url_encode(salt)}${_b64url_encode(derived)}"


def _verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, salt_text, expected_text = encoded_hash.split("$", 2)
        if algorithm != "scrypt":
            return False
        salt = _b64url_decode(salt_text)
        expected = _b64url_decode(expected_text)
        actual = hashlib.scrypt(
            password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=len(expected)
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _create_access_token(user_id: int) -> tuple[str, int]:
    now = int(time.time())
    expires_in = JWT_EXPIRE_MINUTES * 60
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "iss": JWT_ISSUER,
        "iat": now,
        "exp": now + expires_in,
    }
    signing_input = (
        f"{_b64url_encode(json.dumps(header, separators=(',', ':')).encode())}."
        f"{_b64url_encode(json.dumps(payload, separators=(',', ':')).encode())}"
    )
    signature = hmac.new(
        JWT_SECRET_KEY.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256
    ).digest()
    return f"{signing_input}.{_b64url_encode(signature)}", expires_in


def _decode_access_token(token: str) -> int:
    try:
        header_part, payload_part, signature_part = token.split(".")
        signing_input = f"{header_part}.{payload_part}"
        expected_signature = hmac.new(
            JWT_SECRET_KEY.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(_b64url_decode(signature_part), expected_signature):
            raise ValueError("Invalid signature")

        header = json.loads(_b64url_decode(header_part))
        payload = json.loads(_b64url_decode(payload_part))
        if header.get("alg") != "HS256" or payload.get("iss") != JWT_ISSUER:
            raise ValueError("Invalid token claims")
        if int(payload["exp"]) <= int(time.time()):
            raise ValueError("Expired token")
        user_id = int(payload["sub"])
        if user_id <= 0:
            raise ValueError("Invalid subject")
        return user_id
    except (ValueError, TypeError, KeyError, UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = _decode_access_token(credentials.credentials)
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="JWT Authentication API", version="1.0.0", lifespan=lifespan)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["authentication"],
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    username = payload.username.strip().lower()
    email = payload.email.strip().lower()
    if not username or not email or "@" not in email:
        raise HTTPException(status_code=422, detail="A valid username and email are required")

    user = User(
        username=username,
        email=email,
        password_hash=_hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email is already registered",
        )
    return user


@app.post("/auth/login", response_model=TokenResponse, tags=["authentication"])
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    identifier = payload.username.strip().lower()
    user = (
        db.query(User)
        .filter(or_(User.username == identifier, User.email == identifier))
        .first()
    )
    if user is None or not _verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token, expires_in = _create_access_token(user.id)
    return TokenResponse(access_token=token, expires_in=expires_in)


@app.get("/auth/me", response_model=UserResponse, tags=["authentication"])
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
