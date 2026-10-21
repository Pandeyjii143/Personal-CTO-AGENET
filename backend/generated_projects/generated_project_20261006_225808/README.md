# FastAPI JWT Authentication API

A production-ready authentication backend built with FastAPI. It provides persistent user accounts, secure password hashing, JWT-based authorization, environment-driven configuration, database migrations, and automated authentication tests.

## Features

- User registration and authentication
- JWT bearer access tokens
- Protected current-user endpoint
- Secure password hashing with bcrypt
- SQLAlchemy-backed user persistence
- Alembic database migrations
- Pydantic request and response validation
- Environment-based configuration
- Automated tests with pytest
- Interactive OpenAPI documentation

## Technology Stack

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Alembic](https://alembic.sqlalchemy.org/)
- [Pydantic](https://docs.pydantic.dev/)
- [python-jose](https://python-jose.readthedocs.io/)
- [Passlib](https://passlib.readthedocs.io/)
- [pytest](https://docs.pytest.org/)

## Project Structure

text
.
├── app/
│   ├── api/
│   │   ├── dependencies.py
│   │   └── routes/
│   │       └── auth.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   └── user.py
│   ├── schemas/
│   │   ├── auth.py
│   │   └── user.py
│   ├── services/
│   │   └── auth.py
│   └── main.py
├── alembic/
├── tests/
├── .env.example
├── alembic.ini
├── requirements.txt
└── README.md


## Requirements

- Python 3.11 or newer
- PostgreSQL for production, or SQLite for local development
- `pip` and a Python virtual environment

## Installation

Clone the repository and create a virtual environment:

bash
git clone <repository-url>
cd <repository-directory>

python -m venv .venv
source .venv/bin/activate


On Windows PowerShell:

powershell
.venv\Scripts\Activate.ps1


Install dependencies:

bash
pip install -r requirements.txt


## Configuration

Copy the example environment file:

bash
cp .env.example .env


Configure the following values:

env
APP_NAME=FastAPI JWT Authentication API
APP_ENV=development
DEBUG=true

DATABASE_URL=sqlite:///./app.db

JWT_SECRET_KEY=replace-with-a-strong-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30


For PostgreSQL:

env
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/auth_db


Generate a secure JWT secret with:

bash
python -c "import secrets; print(secrets.token_urlsafe(64))"


Never commit `.env` files or production secrets to source control.

## Database Migrations

Apply all migrations before starting the API:

bash
alembic upgrade head


Create a migration after changing SQLAlchemy models:

bash
alembic revision --autogenerate -m "describe the schema change"
alembic upgrade head


Roll back the latest migration:

bash
alembic downgrade -1


## Running the API

Start the development server:

bash
uvicorn app.main:app --reload


The API is available at:

- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI schema: `http://127.0.0.1:8000/openapi.json`

## Authentication Flow

1. Register a user with an email address and password.
2. Log in with valid credentials.
3. Receive a signed JWT access token.
4. Send the token in the `Authorization` header when calling protected endpoints.

http
Authorization: Bearer <access-token>


JWTs contain identity and expiration claims, but must not contain passwords or other sensitive information.

## API Endpoints

| Method | Endpoint | Authentication | Description |
|---|---|---:|---|
| `POST` | `/api/v1/auth/register` | No | Create a user account |
| `POST` | `/api/v1/auth/login` | No | Authenticate and issue an access token |
| `GET` | `/api/v1/auth/me` | Bearer token | Return the authenticated user |

### Register

bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "StrongPassword123!"
  }'


Example response:


{
  "id": 1,
  "email": "user@example.com",
  "is_active": true
}


### Log In

The login endpoint uses OAuth2 password form data. The email address is submitted through the `username` field.

bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=StrongPassword123!"


Example response:


{
  "access_token": "<jwt-access-token>",
  "token_type": "bearer"
}


### Get the Current User

bash
curl http://127.0.0.1:8000/api/v1/auth/me \
  -H "Authorization: Bearer <jwt-access-token>"


## Error Responses

The API uses standard HTTP status codes:

| Status | Meaning |
|---:|---|
| `400` | Invalid request or account already exists |
| `401` | Invalid credentials, missing token, or expired token |
| `403` | Authenticated user is not permitted to access the resource |
| `422` | Request validation failed |
| `500` | Unexpected server error |

Validation errors include field-level details using FastAPI's standard error format.

## Testing

Run the complete test suite:

bash
pytest


Run tests with coverage:

bash
pytest --cov=app --cov-report=term-missing


The authentication suite should cover:

- Successful user registration
- Duplicate account rejection
- Password validation
- Successful and failed login attempts
- Access-token generation
- Protected endpoint access
- Missing, malformed, and expired token rejection
- User password hash persistence

Tests should use an isolated database and must not depend on development or production data.

## Security Considerations

- Passwords are hashed and are never stored or logged in plain text.
- JWT signing secrets are supplied through environment variables.
- Tokens have a limited lifetime and are validated for signature and expiration.
- Authentication failures return generic messages to reduce account enumeration risk.
- Sensitive fields are excluded from API responses.
- HTTPS must be enabled in production.
- Production deployments should use a managed secret store and a dedicated database account.
- Login rate limiting and audit logging are recommended for internet-facing deployments.
- Changing the JWT secret invalidates all tokens signed with the previous secret.

## Production Deployment

Before deploying:

1. Set `APP_ENV=production` and disable debug mode.
2. Use PostgreSQL or another production-grade database.
3. provide a strong JWT secret through a secret manager.
4. Apply migrations with `alembic upgrade head`.
5. Run the application behind HTTPS and a trusted reverse proxy.
6. Configure allowed hosts and CORS origins explicitly.
7. Run tests and security checks in CI.
8. Configure structured logging, monitoring, backups, and alerting.

Example production command:

bash
gunicorn app.main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8000


Worker counts should be tuned according to available CPU, memory, and workload characteristics.

## License

Add the project's license information here.
