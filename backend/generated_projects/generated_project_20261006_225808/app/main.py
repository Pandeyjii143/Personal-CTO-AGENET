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
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field


DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/app.db")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "development-only-change-this-secret")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
PASSWORD_HASH_ITERATIONS = 310_000


def _connect() -> sqlite3.Connection:
    if DATABASE_PATH != ":memory:":
        Path(DATABASE_PATH).expanduser().parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def _initialize_database() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    _initialize_database()
    yield


app = FastAPI(title="JWT Authentication API", lifespan=lifespan)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=256)


class UserPublic(BaseModel):
    id: int
    email: str
    is_active: bool
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


def _normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
        raise HTTPException(status_code=422, detail="Invalid email address")
    return normalized


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
    )
    return "pbkdf2_sha256${}${}${}".format(
        PASSWORD_HASH_ITERATIONS,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def _verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_text, digest_text = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_text.encode("ascii"))
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, int(iterations)
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _create_access_token(user_id: int) -> str:
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    signing_input = f"{_b64url(json.dumps(header, separators=(',', ':')).encode())}.{_b64url(json.dumps(payload, separators=(',', ':')).encode())}"
    signature = hmac.new(
        JWT_SECRET_KEY.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256
    ).digest()
    return f"{signing_input}.{_b64url(signature)}"


def _decode_access_token(token: str) -> int:
    try:
        header_part, payload_part, signature_part = token.split(".")
        signing_input = f"{header_part}.{payload_part}"
        expected_signature = hmac.new(
            JWT_SECRET_KEY.encode("utf-8"),
            signing_input.encode("ascii"),
            hashlib.sha256,
        ).digest()
        supplied_signature = base64.urlsafe_b64decode(
            signature_part + "=" * (-len(signature_part) % 4)
        )
        if not hmac.compare_digest(expected_signature, supplied_signature):
            raise ValueError("Invalid signature")
        header = json.loads(
            base64.urlsafe_b64decode(header_part + "=" * (-len(header_part) % 4))
        )
        payload = json.loads(
            base64.urlsafe_b64decode(payload_part + "=" * (-len(payload_part) % 4))
        )
        if header.get("alg") != JWT_ALGORITHM or int(payload["exp"]) <= int(time.time()):
            raise ValueError("Expired or unsupported token")
        return int(payload["sub"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def _public_user(row: sqlite3.Row) -> UserPublic:
    return UserPublic(
        id=row["id"],
        email=row["email"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
    )


def get_current_user(token: str = Depends(oauth2_scheme)) -> UserPublic:
    user_id = _decode_access_token(token)
    with _connect() as connection:
        row = connection.execute(
            "SELECT id, email, is_active, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    if row is None or not row["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _public_user(row)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/auth/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    tags=["authentication"],
)
def register(user: UserCreate) -> UserPublic:
    email = _normalize_email(user.email)
    password_hash = _hash_password(user.password)
    try:
        with _connect() as connection:
            cursor = connection.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash),
            )
            row = connection.execute(
                "SELECT id, email, is_active, created_at FROM users WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="An account with this email already exists") from exc
    return _public_user(row)


async def _read_login_credentials(request: Request) -> tuple[str, str]:
    content_type = request.headers.get("content-type", "").lower()
    if "application/json" in content_type:
        try:
            body: Any = await request.json()
        except (json.JSONDecodeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="Invalid JSON request body") from exc
        if not isinstance(body, dict):
            raise HTTPException(status_code=422, detail="Expected a JSON object")
        username = body.get("email", body.get("username", ""))
        password = body.get("password", "")
    else:
        form = parse_qs((await request.body()).decode("utf-8"), keep_blank_values=True)
        username = (form.get("username") or form.get("email") or [""])[0]
        password = (form.get("password") or [""])[0]
    if not isinstance(username, str) or not isinstance(password, str) or not username or not password:
        raise HTTPException(status_code=422, detail="Email and password are required")
    return username, password


@app.post("/auth/token", response_model=TokenResponse, tags=["authentication"])
@app.post("/auth/login", response_model=TokenResponse, tags=["authentication"])
async def login(request: Request) -> TokenResponse:
    email, password = await _read_login_credentials(request)
    email = _normalize_email(email)
    with _connect() as connection:
        row = connection.execute(
            "SELECT id, password_hash, is_active FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    if row is None or not _verify_password(password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not row["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
    return TokenResponse(
        access_token=_create_access_token(row["id"]),
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@app.get("/auth/me", response_model=UserPublic, tags=["authentication"])
def read_current_user(current_user: UserPublic = Depends(get_current_user)) -> UserPublic:
    return current_user
