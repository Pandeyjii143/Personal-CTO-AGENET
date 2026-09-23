from passlib.context import CryptContext
from passlib.exc import InvalidHashError


_password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return a secure hash of a plaintext password."""
    if not isinstance(password, str):
        raise TypeError("password must be a string")
    return _password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return whether a plaintext password matches its stored hash."""
    if not isinstance(plain_password, str) or not isinstance(hashed_password, str):
        return False
    try:
        return _password_context.verify(plain_password, hashed_password)
    except (InvalidHashError, ValueError):
        return False


# Common alias used by FastAPI authentication examples.
get_password_hash = hash_password
