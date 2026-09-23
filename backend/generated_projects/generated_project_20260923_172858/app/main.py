import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, field_validator


# Configure with JWT_SECRET_KEY (at least 32 characters) and DATABASE_PATH.
# When no key is configured, a random development key is generated for this process.
_configured_secret = os.getenv("JWT_SECRET_KEY")
if _configured_secret and len(_configured_secret.encode("utf-8")) < 32:
    raise RuntimeError("JWT_SECRET_KEY must be at least 32 bytes long")
JWT_SECRET_KEY = (_configured_secret or secrets.token_urlsafe(48)).encode("utf-8")
JWT_ISSUER = os.getenv("JWT_ISSUER", "fastapi-auth")
ACCESS_TOKEN_EXPIRE_SECONDS = int(os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", "3600"))
if ACCESS_TOKEN_EXPIRE_SECONDS <= 0:
    raise RuntimeError("ACCESS_TOKEN_EXPIRE_SECONDS must be greater than zero")

DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "./app.db")).expanduser()
if str(DATABASE_PATH) != ":memory:":
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

PASSWORD_HASH_ITERATIONS = 310_000
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(str(DATABASE_PATH), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


initialize_database()


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_access_token(user_id: int) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "iss": JWT_ISSUER,
        "iat": now,
        "exp": now + ACCESS_TOKEN_EXPIRE_SECONDS,
    }
    signing_input = (
        f"{_b64url_encode(json.dumps(header, separators=(',', ':')).encode())}."
        f"{_b64url_encode(json.dumps(payload, separators=(',', ':')).encode())}"
    )
    signature = hmac.new(JWT_SECRET_KEY, signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
        signing_input = f"{header_segment}.{payload_segment}"
        supplied_signature = _b64url_decode(signature_segment)
        expected_signature = hmac.new(
            JWT_SECRET_KEY, signing_input.encode("ascii"), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(supplied_signature, expected_signature):
            raise ValueError("Invalid signature")

        header = json.loads(_b64url_decode(header_segment))
        claims = json.loads(_b64url_decode(payload_segment))
        if not isinstance(header, dict) or header.get("alg") != "HS256":
            raise ValueError("Unsupported token algorithm")
        if not isinstance(claims, dict) or claims.get("iss") != JWT_ISSUER:
            raise ValueError("Invalid token issuer")
        if not isinstance(claims.get("sub"), str) or not claims["sub"].isdigit():
            raise ValueError("Invalid token subject")
        if not isinstance(claims.get("exp"), int) or claims["exp"] <= int(time.time()):
            raise ValueError("Expired token")
        if not isinstance(claims.get("iat"), int) or claims["iat"] > int(time.time()) + 60:
            raise ValueError("Invalid token issue time")
        return claims
    except (ValueError, TypeError, KeyError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
    )
    return f"pbkdf2_sha256${PASSWORD_HASH_ITERATIONS}${_b64url_encode(salt)}${_b64url_encode(digest)}"


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt_text, digest_text = encoded_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        if iterations < 100_000 or iterations > 2_000_000:
            return False
        salt = _b64url_decode(salt_text)
        expected = _b64url_decode(digest_text)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


class RegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.lower()
        if not EMAIL_PATTERN.fullmatch(value):
            raise ValueError("A valid email address is required")
        return value


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.lower()
        if not EMAIL_PATTERN.fullmatch(value):
            raise ValueError("A valid email address is required")
        return value


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> UserResponse:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = decode_access_token(credentials.credentials)
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, email, created_at FROM users WHERE id = ?",
            (int(claims["sub"]),),
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return UserResponse(
        id=row["id"], email=row["email"], created_at=datetime.fromisoformat(row["created_at"])
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="JWT Authentication API", lifespan=lifespan)


@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest) -> UserResponse:
    password_hash = hash_password(payload.password)
    created_at = datetime.now(timezone.utc).isoformat()
    try:
        with get_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
                (payload.email, password_hash, created_at),
            )
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        ) from exc

    return UserResponse(id=user_id, email=payload.email, created_at=datetime.fromisoformat(created_at))


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, password_hash FROM users WHERE email = ? COLLATE NOCASE",
            (payload.email,),
        ).fetchone()

    if row is None or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=create_access_token(row["id"]),
        expires_in=ACCESS_TOKEN_EXPIRE_SECONDS,
    )


@app.get("/auth/me", response_model=UserResponse)
def get_me(current_user: Annotated[UserResponse, Depends(get_current_user)]) -> UserResponse:
    return current_user
