import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from jose import JWTError, jwt


# Configure SECRET_KEY in the environment with a cryptographically random value
# of at least 32 bytes. The key is checked when tokens are created or decoded,
# rather than at import time, so the module can be imported by tooling and tests.
SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = "HS256"

try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
except ValueError as exc:
    raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be an integer") from exc

if ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
    raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be greater than zero")

_PASSWORD_HASH_NAME = "pbkdf2_sha256"
_PASSWORD_HASH_ITERATIONS = 600_000
_PASSWORD_SALT_BYTES = 16
_PASSWORD_DERIVED_KEY_BYTES = 32


def _get_secret_key() -> str:
    key = os.getenv("SECRET_KEY", SECRET_KEY)
    if not key or len(key.encode("utf-8")) < 32:
        raise RuntimeError("SECRET_KEY must be configured with at least 32 bytes")
    return key


def get_password_hash(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 and a unique random salt."""
    if not isinstance(password, str):
        raise TypeError("password must be a string")

    salt = secrets.token_bytes(_PASSWORD_SALT_BYTES)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PASSWORD_HASH_ITERATIONS,
        dklen=_PASSWORD_DERIVED_KEY_BYTES,
    )
    encode = lambda value: base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")
    return "$".join(
        (
            _PASSWORD_HASH_NAME,
            str(_PASSWORD_HASH_ITERATIONS),
            encode(salt),
            encode(derived_key),
        )
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return whether a plaintext password matches a hash from get_password_hash."""
    if not isinstance(plain_password, str) or not isinstance(hashed_password, str):
        return False

    try:
        scheme, iterations_text, salt_text, expected_text = hashed_password.split("$")
        if scheme != _PASSWORD_HASH_NAME:
            return False
        iterations = int(iterations_text)
        if not 1 <= iterations <= 10_000_000:
            return False

        def decode(value: str) -> bytes:
            return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

        salt = decode(salt_text)
        expected = decode(expected_text)
        if not salt or len(expected) != _PASSWORD_DERIVED_KEY_BYTES:
            return False

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt,
            iterations,
            dklen=len(expected),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, UnicodeError):
        return False


def create_access_token(
    data: Mapping[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed access token, adding an expiration claim if absent."""
    if not isinstance(data, Mapping):
        raise TypeError("data must be a mapping")

    now = datetime.now(timezone.utc)
    payload = dict(data)
    payload.setdefault(
        "exp",
        now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)),
    )
    payload.setdefault("iat", now)
    return jwt.encode(payload, _get_secret_key(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Validate and decode an access token; raises jose.JWTError if invalid."""
    if not isinstance(token, str) or not token:
        raise JWTError("Token must be a non-empty string")
    return jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])


def verify_access_token(token: str) -> dict[str, Any] | None:
    """Validate a token, returning its claims or None when it is invalid."""
    try:
        return decode_access_token(token)
    except JWTError:
        return None
