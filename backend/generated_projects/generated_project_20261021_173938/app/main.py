from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from contextlib import asynccontextmanager
from typing import Any, Generator

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, ForeignKey, Integer, String, create_engine, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Settings:
    database_url = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    jwt_secret = os.getenv("JWT_SECRET_KEY", "change-this-secret-in-production")
    jwt_issuer = os.getenv("JWT_ISSUER", "fastapi-auth")
    access_token_ttl_seconds = int(os.getenv("ACCESS_TOKEN_TTL_SECONDS", "900"))
    refresh_token_ttl_seconds = int(os.getenv("REFRESH_TOKEN_TTL_SECONDS", "2592000"))
    password_iterations = int(os.getenv("PASSWORD_HASH_ITERATIONS", "310000"))
    auto_create_schema = os.getenv("AUTO_CREATE_SCHEMA", "true").lower() == "true"


settings = Settings()
if settings.jwt_secret == "change-this-secret-in-production" and os.getenv("ENVIRONMENT", "development").lower() == "production":
    raise RuntimeError("JWT_SECRET_KEY must be set in production")

_engine_options: dict[str, Any] = {"pool_pre_ping": True}
if settings.database_url.startswith("sqlite"):
    _engine_options["connect_args"] = {"check_same_thread": False}
engine = create_engine(settings.database_url, **_engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    jti: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    expires_at: Mapped[int] = mapped_column(Integer, nullable=False)
    revoked_at: Mapped[int | None] = mapped_column(Integer, nullable=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, settings.password_iterations)
    return f"pbkdf2_sha256${settings.password_iterations}${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), _b64decode(salt), int(iterations))
        return hmac.compare_digest(_b64encode(actual), expected)
    except (ValueError, TypeError):
        return False


def create_jwt(*, subject: int, token_type: str, ttl_seconds: int, jti: str | None = None) -> tuple[str, dict[str, Any]]:
    now = int(time.time())
    claims: dict[str, Any] = {
        "sub": str(subject),
        "iss": settings.jwt_issuer,
        "iat": now,
        "exp": now + ttl_seconds,
        "jti": jti or secrets.token_urlsafe(18),
        "type": token_type,
    }
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = f"{_b64encode(json.dumps(header, separators=(',', ':')).encode())}.{_b64encode(json.dumps(claims, separators=(',', ':')).encode())}"
    signature = hmac.new(settings.jwt_secret.encode(), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64encode(signature)}", claims


def decode_jwt(token: str, expected_type: str) -> dict[str, Any]:
    try:
        header_part, payload_part, signature_part = token.split(".")
        signing_input = f"{header_part}.{payload_part}"
        expected_signature = hmac.new(settings.jwt_secret.encode(), signing_input.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64decode(signature_part), expected_signature):
            raise ValueError("Invalid signature")
        header = json.loads(_b64decode(header_part))
        claims = json.loads(_b64decode(payload_part))
        now = int(time.time())
        if header.get("alg") != "HS256" or claims.get("iss") != settings.jwt_issuer:
            raise ValueError("Invalid token")
        if claims.get("type") != expected_type or int(claims["exp"]) <= now:
            raise ValueError("Expired or incorrect token")
        if not claims.get("sub") or not claims.get("jti"):
            raise ValueError("Missing token claims")
        return claims
    except (ValueError, TypeError, KeyError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def issue_token_pair(db: Session, user: User) -> dict[str, Any]:
    access_token, _ = create_jwt(
        subject=user.id,
        token_type="access",
        ttl_seconds=settings.access_token_ttl_seconds,
    )
    refresh_jti = secrets.token_urlsafe(24)
    refresh_token, refresh_claims = create_jwt(
        subject=user.id,
        token_type="refresh",
        ttl_seconds=settings.refresh_token_ttl_seconds,
        jti=refresh_jti,
    )
    db.add(RefreshToken(jti=refresh_jti, user_id=user.id, expires_at=refresh_claims["exp"]))
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_ttl_seconds,
    }


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized()
    claims = decode_jwt(credentials.credentials, "access")
    try:
        user_id = int(claims["sub"])
    except (ValueError, TypeError) as exc:
        raise unauthorized() from exc
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized()
    return user


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)

    def normalized_email(self) -> str:
        value = self.email.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise HTTPException(status_code=422, detail="A valid email address is required")
        return value


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Set AUTO_CREATE_SCHEMA=false when schema changes are managed by Alembic migrations.
    if settings.auto_create_schema:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="JWT Authentication API", version="1.0.0", lifespan=lifespan)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["auth"])
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    email = payload.normalized_email()
    user = User(email=email, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists") from exc
    return user


@app.post("/auth/login", response_model=TokenResponse, tags=["auth"])
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    email = payload.email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise unauthorized()
    tokens = issue_token_pair(db, user)
    db.commit()
    return tokens


@app.post("/auth/refresh", response_model=TokenResponse, tags=["auth"])
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    claims = decode_jwt(payload.refresh_token, "refresh")
    try:
        user_id = int(claims["sub"])
    except (ValueError, TypeError) as exc:
        raise unauthorized() from exc

    now = int(time.time())
    result = db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.jti == claims["jti"],
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        .values(revoked_at=now)
    )
    if result.rowcount != 1:
        db.rollback()
        raise unauthorized()

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        db.rollback()
        raise unauthorized()
    tokens = issue_token_pair(db, user)
    db.commit()
    return tokens


@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT, tags=["auth"])
def logout(payload: RefreshRequest, db: Session = Depends(get_db)) -> None:
    claims = decode_jwt(payload.refresh_token, "refresh")
    try:
        user_id = int(claims["sub"])
    except (ValueError, TypeError) as exc:
        raise unauthorized() from exc
    db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.jti == claims["jti"],
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=int(time.time()))
    )
    db.commit()
    return None


@app.get("/users/me", response_model=UserResponse, tags=["users"])
def read_current_user(user: User = Depends(get_current_user)) -> User:
    return user
