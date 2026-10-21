# FastAPI JWT Authentication

Production-oriented authentication backend built with FastAPI. It provides user persistence, secure password hashing, JWT access and refresh tokens, configuration management, database migrations, and automated authentication tests.

## Features

- User registration and authentication
- Short-lived JWT access tokens
- Long-lived JWT refresh tokens
- Refresh token rotation and revocation support
- Secure password hashing using Argon2 or bcrypt
- SQLAlchemy-based user persistence
- Alembic database migrations
- Environment-based configuration
- Protected FastAPI routes
- OpenAPI and Swagger UI integration
- Automated tests with pytest
- Consistent authentication error responses

## Authentication Flow

1. A user registers with an email and password.
2. The password is hashed before being stored in the database.
3. The user signs in and receives an access token and a refresh token.
4. The access token is included in protected requests:

   http
   Authorization: Bearer <access_token>
   

5. When the access token expires, the refresh token is exchanged for a new token pair.
6. Logout revokes the refresh token so it cannot be reused.

Access tokens should be short-lived. Refresh tokens should be stored securely and rotated whenever they are used.

## Technology Stack

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Alembic](https://alembic.sqlalchemy.org/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [PyJWT](https://pyjwt.readthedocs.io/) or `python-jose`
- [pwdlib](https://frankie567.github.io/pwdlib/) or Passlib
- [pytest](https://docs.pytest.org/)
- PostgreSQL for production; SQLite may be used for local development and tests

## Project Structure

text
.
├── alembic/
│   └── versions/             # Database migration revisions
├── app/
│   ├── api/
│   │   ├── dependencies.py   # Authentication dependencies
│   │   └── routes/
│   │       ├── auth.py       # Register, login, refresh, and logout
│   │       └── users.py      # User endpoints
│   ├── core/
│   │   ├── config.py         # Environment configuration
│   │   └── security.py       # Password and JWT utilities
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   ├── refresh_token.py
│   │   └── user.py
│   ├── schemas/
│   │   ├── auth.py
│   │   └── user.py
│   ├── services/
│   │   └── auth.py           # Authentication business logic
│   └── main.py               # FastAPI application
├── tests/
│   ├── conftest.py
│   └── test_auth.py
├── alembic.ini
├── pyproject.toml
├── .env.example
└── README.md


The exact structure may vary, but API, persistence, configuration, and security concerns should remain separated.

## Requirements

- Python 3.11 or later
- PostgreSQL 14 or later for production
- A Python environment manager such as `venv`, Poetry, or uv

## Installation

Clone the repository and enter the project directory:

bash
git clone <repository-url>
cd <repository-directory>


Create and activate a virtual environment:

bash
python -m venv .venv
source .venv/bin/activate


On Windows PowerShell:

powershell
.venv\Scripts\Activate.ps1


Install the dependencies using the dependency manager configured by the project:

bash
pip install -r requirements.txt


Or, when using Poetry or uv:

bash
poetry install
# or
uv sync


## Configuration

Copy the example environment file:

bash
cp .env.example .env


Example configuration:

dotenv
APP_NAME=FastAPI JWT Authentication
APP_ENV=development
DEBUG=true

DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/auth_db

JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Optional, when access and refresh tokens use separate signing keys
JWT_REFRESH_SECRET_KEY=replace-with-another-long-random-secret


Generate a secure signing secret with:

bash
python -c "import secrets; print(secrets.token_urlsafe(64))"


Do not commit `.env` files or production secrets to source control. In production, obtain secrets from a managed secret store.

### Important Settings

| Variable | Description | Example |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy database connection URL | `postgresql+psycopg://user:pass@db/auth` |
| `JWT_SECRET_KEY` | Secret used to sign access tokens | Random 64-byte value |
| `JWT_REFRESH_SECRET_KEY` | Optional separate refresh-token secret | Random 64-byte value |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh-token lifetime | `7` |

## Database Migrations

Create the configured database, then apply migrations:

bash
alembic upgrade head


Create a new migration after changing a model:

bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head


Inspect migration files before applying them, especially in production.

## Running the Application

Start the development server:

bash
uvicorn app.main:app --reload


The application is available at:

- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

For production, run behind a reverse proxy and use an appropriate process manager:

bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4


## API Endpoints

The examples below assume an `/api/v1` prefix.

| Method | Endpoint | Authentication | Description |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/register` | Public | Register a user |
| `POST` | `/api/v1/auth/login` | Public | Authenticate and issue tokens |
| `POST` | `/api/v1/auth/refresh` | Refresh token | Rotate tokens |
| `POST` | `/api/v1/auth/logout` | Refresh token | Revoke a refresh token |
| `GET` | `/api/v1/users/me` | Access token | Return the current user |

### Register

bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "user@example.com",
    "password": "StrongPassword123!"
  }'


Example response:


{
  "id": "e0fb8ce2-49e8-4aa5-9172-145f75f3150e",
  "email": "user@example.com",
  "is_active": true
}


### Login

bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "user@example.com",
    "password": "StrongPassword123!"
  }'


Example response:


{
  "access_token": "<access-token>",
  "refresh_token": "<refresh-token>",
  "token_type": "bearer",
  "expires_in": 900
}


If the login endpoint uses OAuth2 form data, submit `username` and `password` instead:

bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=user@example.com&password=StrongPassword123!'


### Access a Protected Endpoint

bash
curl http://127.0.0.1:8000/api/v1/users/me \
  -H 'Authorization: Bearer <access-token>'


### Refresh Tokens

bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/refresh \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token": "<refresh-token>"}'


A successful refresh should invalidate the submitted refresh token and return a new access and refresh token pair.

### Logout

bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/logout \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token": "<refresh-token>"}'


## JWT Claims

Tokens should contain only the minimum claims required for validation and authorization:

| Claim | Purpose |
| --- | --- |
| `sub` | User identifier |
| `type` | Distinguishes `access` and `refresh` tokens |
| `jti` | Unique token identifier used for rotation or revocation |
| `iat` | Token issue time |
| `exp` | Token expiration time |
| `iss` | Optional token issuer |
| `aud` | Optional intended audience |

The server must reject expired tokens, tokens with an unexpected type, invalid signatures, revoked refresh tokens, and tokens belonging to inactive users.

## Testing

Run the full test suite:

bash
pytest


Run with coverage:

bash
pytest --cov=app --cov-report=term-missing


Authentication tests should cover:

- Successful registration
- Duplicate email rejection
- Password hashing and verification
- Successful and unsuccessful login
- Access to protected routes
- Missing, malformed, and expired access tokens
- Refresh-token validation and rotation
- Refresh-token reuse detection
- Logout and token revocation
- Inactive or deleted users
- Invalid token type and signature

Tests should use a dedicated database and must never run against production data.

## Security Considerations

- Passwords are stored only as strong salted hashes, never as plaintext.
- JWT signing secrets must be long, random, and managed outside source control.
- Access and refresh tokens must have separate purposes and expiration policies.
- Validate the token signature, algorithm, expiration, type, issuer, and audience where configured.
- Store refresh-token identifiers or cryptographic hashes rather than raw refresh tokens.
- Rotate refresh tokens after every successful refresh.
- Revoke the entire token family when reuse of an invalidated refresh token is detected.
- Return generic login errors to reduce account enumeration risk.
- Apply rate limiting to registration, login, and refresh endpoints.
- Use HTTPS in every non-local environment.
- For browser clients, prefer `Secure`, `HttpOnly`, and appropriately configured `SameSite` cookies for refresh tokens.
- If authentication uses cookies, implement CSRF protection.
- Configure CORS with explicit trusted origins; do not combine wildcard origins with credentials.
- Plan signing-key rotation and secret replacement before production deployment.

## Error Responses

Authentication failures use standard HTTP status codes:

| Status | Meaning |
| --- | --- |
| `400 Bad Request` | Invalid registration or refresh request |
| `401 Unauthorized` | Missing, invalid, expired, or revoked credentials |
| `403 Forbidden` | Authenticated user lacks permission or is inactive |
| `409 Conflict` | A user with the supplied identity already exists |
| `422 Unprocessable Entity` | Request validation failed |
| `429 Too Many Requests` | Authentication rate limit exceeded |

Example error response:


{
  "detail": "Invalid authentication credentials"
}


## Production Checklist

- Use PostgreSQL or another production-grade database.
- Set `DEBUG=false`.
- Replace all development secrets.
- Enable HTTPS and secure response headers.
- Restrict CORS to trusted origins.
- Apply all migrations before serving traffic.
- Configure structured logging and error monitoring.
- Add rate limiting and brute-force protection.
- Back up the database and test restoration procedures.
- Run tests and dependency vulnerability scans in CI.
- Use asymmetric signing such as RS256 or ES256 when multiple services verify tokens independently.

## License

Add the project license here.