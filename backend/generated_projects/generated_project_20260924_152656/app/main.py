"""FastAPI JWT authentication application.

Configuration is provided through environment variables:
  APP_ENV, APP_NAME, DATABASE_PATH, JWT_SECRET_KEY, JWT_ISSUER,
  ACCESS_TOKEN_EXPIRE_MINUTES, and CORS_ORIGINS.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import sqlite3
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field


APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
APP_NAME = os.getenv("APP_NAME", "JWT Authentication API")
DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/app.db")
JWT_ISSUER = os.getenv("JWT_ISSUER", APP_NAME)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "development-only-change-this-secret-key")

if ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
    raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be a positive integer")
if APP_ENV == "production" and (
    JWT_SECRET_KEY == "development-only-change-this-secret-key"
    or len(JWT_SECRET_KEY.encode("utf-8")) < 32
):
    raise RuntimeError("Production requires a JWT_SECRET_KEY of at least 32 bytes")


def _database_connection() -> sqlite3.Connection:
    path = Path(DATABASE_PATH).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def _run_migrations() -> None:
    """Apply idempotent SQLite schema migrations at application startup."""
    with _database_connection() as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(version INTEGER PRIMARY KEY, applied_at INTEGER NOT NULL)"
        )
        applied = {
            row[0]
            for row in connection.execute("SELECT version FROM schema_migrations").fetchall()
        }
        if 1 not in applied:
            connection.execute(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                )
                """
            )
            connection.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (1, int(time.time())),
            )


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _create_access_token(user_id: int) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "iss": JWT_ISSUER,
        "iat": now,
        "exp": now + ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
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
        expected_signature = hmac.new(
            JWT_SECRET_KEY.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256
        ).digest()
        supplied_signature = _b64url_decode(encoded_signature)
        if not hmac.compare_digest(expected_signature, supplied_signature):
            raise ValueError("Invalid signature")

        header = json.loads(_b64url_decode(encoded_header))
        payload = json.loads(_b64url_decode(encoded_payload))
        if header.get("alg") != "HS256" or not isinstance(payload, dict):
            raise ValueError("Invalid token")
        if payload.get("iss") != JWT_ISSUER:
            raise ValueError("Invalid issuer")
        if not isinstance(payload.get("exp"), int) or payload["exp"] <= int(time.time()):
            raise ValueError("Expired token")
        if not isinstance(payload.get("sub"), str) or not payload["sub"].isdigit():
            raise ValueError("Invalid subject")
        return payload
    except (ValueError, TypeError, KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32
    )
    return f"scrypt$16384$8$1${_b64url_encode(salt)}${_b64url_encode(derived)}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, n, r, p, salt_text, hash_text = stored_hash.split("$")
        if algorithm != "scrypt":
            return False
        expected = _b64url_decode(hash_text)
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=_b64url_decode(salt_text),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, MemoryError):
        return False


class UserCredentials(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=128)


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


bearer_scheme = HTTPBearer(auto_error=False)


_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if not _EMAIL_PATTERN.fullmatch(normalized):
        raise HTTPException(status_code=422, detail="A valid email address is required")
    return normalized


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> UserResponse:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer access token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = _decode_access_token(credentials.credentials)
    with _database_connection() as connection:
        row = connection.execute(
            "SELECT id, email, created_at FROM users WHERE id = ?",
            (int(payload["sub"]),),
        ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return UserResponse(**dict(row))


@asynccontextmanager
async def lifespan(_: FastAPI):
    _run_migrations()
    yield


app = FastAPI(title=APP_NAME, lifespan=lifespan)

_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]
if _origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["authentication"],
)
def register(credentials: UserCredentials) -> UserResponse:
    email = _normalize_email(credentials.email)
    now = int(time.time())
    password_hash = _hash_password(credentials.password)
    try:
        with _database_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
                (email, password_hash, now),
            )
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="An account with this email already exists") from exc
    return UserResponse(id=user_id, email=email, created_at=now)


@app.post("/auth/login", response_model=TokenResponse, tags=["authentication"])
def login(credentials: UserCredentials) -> TokenResponse:
    email = _normalize_email(credentials.email)
    with _database_connection() as connection:
        row = connection.execute(
            "SELECT id, password_hash FROM users WHERE email = ? COLLATE NOCASE", (email,)
        ).fetchone()

    # Perform a password hash even for unknown users to reduce account-enumeration timing leaks.
    valid_password = _verify_password(credentials.password, row["password_hash"]) if row else False
    if row is None:
        _hash_password(credentials.password)
    if not valid_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=_create_access_token(int(row["id"])),
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@app.get("/auth/me", response_model=UserResponse, tags=["authentication"])
def read_current_user(current_user: Annotated[UserResponse, Depends(get_current_user)]) -> UserResponse:
    return current_user
