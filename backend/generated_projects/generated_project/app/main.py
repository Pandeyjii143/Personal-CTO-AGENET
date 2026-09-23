"""FastAPI JWT authentication application.

Configuration is read from the environment:
- JWT_SECRET_KEY: HS256 signing key (use a unique secret of at least 32 characters).
- JWT_ACCESS_TOKEN_EXPIRE_MINUTES: access-token lifetime (default: 30).
- AUTH_DATABASE_PATH: SQLite database path (default: auth.db).
"""

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
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field


JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "development-only-change-this-secret-key-before-deploying",
)
if len(JWT_SECRET_KEY.encode("utf-8")) < 32:
    raise RuntimeError("JWT_SECRET_KEY must be at least 32 bytes long")

JWT_ISSUER = os.getenv("JWT_ISSUER", "fastapi-auth")
try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
except ValueError as exc:
    raise RuntimeError("JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be an integer") from exc
if ACCESS_TOKEN_EXPIRE_MINUTES < 1:
    raise RuntimeError("JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be at least 1")

DATABASE_PATH = os.getenv("AUTH_DATABASE_PATH", "auth.db")
_PASSWORD_ITERATIONS = 310_000
_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_bearer = HTTPBearer(auto_error=False)


def _connect() -> sqlite3.Connection:
    if DATABASE_PATH != ":memory:":
        Path(DATABASE_PATH).expanduser().resolve().parent.mkdir(
            parents=True, exist_ok=True
        )
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _initialize_database() -> None:
    connection = _connect()
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _create_access_token(user_id: str) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "iss": JWT_ISSUER,
        "iat": now,
        "exp": now + ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "jti": secrets.token_urlsafe(16),
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
        if len(token) > 8192:
            raise ValueError("Token is too large")
        header_part, payload_part, signature_part = token.split(".")
        signing_input = f"{header_part}.{payload_part}"
        expected_signature = hmac.new(
            JWT_SECRET_KEY.encode("utf-8"),
            signing_input.encode("ascii"),
            hashlib.sha256,
        ).digest()
        supplied_signature = _b64url_decode(signature_part)
        if not hmac.compare_digest(expected_signature, supplied_signature):
            raise ValueError("Invalid signature")

        header = json.loads(_b64url_decode(header_part))
        payload = json.loads(_b64url_decode(payload_part))
        if not isinstance(header, dict) or header.get("alg") != "HS256":
            raise ValueError("Unsupported token algorithm")
        if not isinstance(payload, dict):
            raise ValueError("Invalid token payload")
        if payload.get("iss") != JWT_ISSUER:
            raise ValueError("Invalid token issuer")
        if not isinstance(payload.get("sub"), str) or not payload["sub"]:
            raise ValueError("Invalid token subject")
        if type(payload.get("exp")) is not int or payload["exp"] <= int(time.time()):
            raise ValueError("Token expired")
        if type(payload.get("iat")) is not int or payload["iat"] > int(time.time()) + 60:
            raise ValueError("Invalid token issue time")
        return payload
    except (ValueError, TypeError, KeyError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PASSWORD_ITERATIONS
    )
    return f"pbkdf2_sha256${_PASSWORD_ITERATIONS}${_b64url_encode(salt)}${_b64url_encode(digest)}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            _b64url_decode(salt),
            int(iterations),
        )
        return hmac.compare_digest(actual, _b64url_decode(expected))
    except (ValueError, TypeError):
        return False


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: str
    email: str
    created_at: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


def _public_user(row: sqlite3.Row) -> UserResponse:
    return UserResponse(
        id=row["id"], email=row["email"], created_at=row["created_at"]
    )


def _get_user_by_id(user_id: str) -> sqlite3.Row | None:
    connection = _connect()
    try:
        return connection.execute(
            "SELECT id, email, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    finally:
        connection.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> UserResponse:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = _decode_access_token(credentials.credentials)
    row = _get_user_by_id(payload["sub"])
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _public_user(row)


@asynccontextmanager
async def lifespan(_: FastAPI):
    _initialize_database()
    yield


app = FastAPI(title="JWT Authentication API", lifespan=lifespan)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["authentication"],
)
def register(request: RegisterRequest) -> UserResponse:
    email = request.email.strip().casefold()
    if not _EMAIL_PATTERN.fullmatch(email):
        raise HTTPException(status_code=422, detail="A valid email address is required")

    user_id = str(uuid.uuid4())
    created_at = int(time.time())
    password_hash = _hash_password(request.password)
    connection = _connect()
    try:
        with connection:
            connection.execute(
                "INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (user_id, email, password_hash, created_at),
            )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        ) from exc
    finally:
        connection.close()

    return UserResponse(id=user_id, email=email, created_at=created_at)


@app.post(
    "/auth/login",
    response_model=TokenResponse,
    tags=["authentication"],
)
def login(request: LoginRequest) -> TokenResponse:
    email = request.email.strip().casefold()
    connection = _connect()
    try:
        row = connection.execute(
            "SELECT id, email, password_hash, created_at FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    finally:
        connection.close()

    if row is None or not _verify_password(request.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=_create_access_token(row["id"]),
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@app.get(
    "/auth/me",
    response_model=UserResponse,
    tags=["authentication"],
)
def get_me(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    return current_user
