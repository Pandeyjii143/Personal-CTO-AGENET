"""FastAPI JWT authentication application with SQLite persistence."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import asynccontextmanager, closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, validator


# Configure JWT_SECRET_KEY in production. A process-local key is used otherwise,
# so development tokens are invalidated whenever the application restarts.
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or secrets.token_urlsafe(48)
JWT_ISSUER = os.getenv("JWT_ISSUER", "fastapi-auth")
DATABASE_PATH = os.getenv("DATABASE_PATH", "./auth.db")

try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
except ValueError as exc:
    raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be an integer") from exc

if ACCESS_TOKEN_EXPIRE_MINUTES < 1:
    raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be at least 1")


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)

    @validator("email")
    def validate_and_normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("A valid email address is required")
        return value

    class Config:
        extra = "forbid"


class RegisterRequest(Credentials):
    pass


class LoginRequest(Credentials):
    pass


class UserResponse(BaseModel):
    id: str
    email: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@contextmanager
def _database() -> Iterator[sqlite3.Connection]:
    path = DATABASE_PATH
    if path != ":memory:":
        Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _initialize_database() -> None:
    with _database() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived_key = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32
    )
    return "$".join(
        (
            "scrypt",
            "16384",
            "8",
            "1",
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(derived_key).decode("ascii"),
        )
    )


def _verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, n, r, p, salt_text, key_text = encoded_hash.split("$", 5)
        if algorithm != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected = base64.urlsafe_b64decode(key_text.encode("ascii"))
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, UnicodeError):
        return False


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _create_access_token(user_id: str) -> str:
    now = int(time.time())
    payload = {
        "iss": JWT_ISSUER,
        "sub": user_id,
        "iat": now,
        "exp": now + ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "jti": secrets.token_urlsafe(16),
    }
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = (
        f"{_b64url_encode(json.dumps(header, separators=(',', ':')).encode())}."
        f"{_b64url_encode(json.dumps(payload, separators=(',', ':')).encode())}"
    )
    signature = hmac.new(
        JWT_SECRET_KEY.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256
    ).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def _decode_access_token(token: str) -> dict[str, Any]:
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".")
        signing_input = f"{encoded_header}.{encoded_payload}"
        supplied_signature = _b64url_decode(encoded_signature)
        expected_signature = hmac.new(
            JWT_SECRET_KEY.encode("utf-8"),
            signing_input.encode("ascii"),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(supplied_signature, expected_signature):
            raise ValueError("Invalid signature")

        header = json.loads(_b64url_decode(encoded_header))
        payload = json.loads(_b64url_decode(encoded_payload))
        if not isinstance(header, dict) or header.get("alg") != "HS256":
            raise ValueError("Unsupported token algorithm")
        if header.get("typ") != "JWT" or not isinstance(payload, dict):
            raise ValueError("Invalid token")
        if payload.get("iss") != JWT_ISSUER:
            raise ValueError("Invalid token issuer")
        if not isinstance(payload.get("sub"), str) or not payload["sub"]:
            raise ValueError("Invalid token subject")
        if not isinstance(payload.get("exp"), int) or payload["exp"] <= int(time.time()):
            raise ValueError("Expired token")
        if not isinstance(payload.get("iat"), int) or payload["iat"] > int(time.time()) + 30:
            raise ValueError("Invalid token issue time")
        return payload
    except (ValueError, TypeError, KeyError, UnicodeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserResponse:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = _decode_access_token(credentials.credentials)
    with _database() as connection:
        row = connection.execute(
            "SELECT id, email, created_at FROM users WHERE id = ?",
            (claims["sub"],),
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return UserResponse(
        id=row["id"], email=row["email"], created_at=row["created_at"]
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    _initialize_database()
    yield


app = FastAPI(
    title="JWT Authentication API",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(data: RegisterRequest) -> UserResponse:
    user_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    password_hash = _hash_password(data.password)

    try:
        with _database() as connection:
            connection.execute(
                "INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (user_id, data.email, password_hash, created_at),
            )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        ) from exc

    return UserResponse(id=user_id, email=data.email, created_at=created_at)


@app.post("/auth/login", response_model=TokenResponse)
def login(data: LoginRequest) -> TokenResponse:
    with _database() as connection:
        row = connection.execute(
            "SELECT id, password_hash FROM users WHERE email = ? COLLATE NOCASE",
            (data.email,),
        ).fetchone()

    if row is None or not _verify_password(data.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=_create_access_token(row["id"]),
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@app.get("/auth/me", response_model=UserResponse)
def read_current_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    return current_user
