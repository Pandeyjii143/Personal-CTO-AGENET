# FastAPI JWT Authentication

A production-ready authentication backend built with FastAPI. The service provides user registration, secure password storage, JWT-based authentication, persistent database storage, schema migrations, configuration management, and automated authentication tests.

## Features

- User registration and authentication
- JWT access-token generation and validation
- Protected API endpoints
- Secure password hashing
- Persistent user storage with SQLAlchemy
- Database migrations with Alembic
- Environment-based configuration
- Request and response validation with Pydantic
- Interactive OpenAPI documentation
- Automated authentication tests with pytest

## Technology Stack

- **FastAPI** — API framework
- **Uvicorn** — ASGI server
- **SQLAlchemy** — ORM and database access
- **Alembic** — database migrations
- **Pydantic Settings** — environment configuration
- **PyJWT / python-jose** — JWT encoding and validation
- **Passlib / pwdlib** — password hashing
- **pytest** — automated testing

## Project Structure

text
.
├── alembic/
│   └── versions/             # Database migration revisions
├── app/
│   ├── api/
│   │   ├── dependencies.py   # Authentication and database dependencies
│   │   └── routes/
│   │       ├── auth.py       # Registration and login endpoints
│   │       └── users.py      # User endpoints
│   ├── core/
│   │   ├── config.py         # Application settings
│   │   └── security.py       # Password and JWT utilities
│   ├── db/
│   │   ├── base.py           # SQLAlchemy declarative base
│   │   └── session.py        # Database session management
│   ├── models/
│   │   └── user.py           # User database model
│   ├── schemas/
│   │   ├── auth.py           # Token schemas
│   │   └── user.py           # User request and response schemas
│   └── main.py               # FastAPI application entry point
├── tests/
│   └── test_auth.py          # Authentication tests
├── .env.example
├── alembic.ini
├── pyproject.toml
└── README.md


> The exact layout may differ slightly depending on the package and dependency configuration used by the project.

## Requirements

- Python 3.11 or newer
- PostgreSQL, SQLite, or another SQLAlchemy-supported database
- A Python virtual environment

## Getting Started

### 1. Clone the repository

bash
git clone <repository-url>
cd <repository-directory>


### 2. Create a virtual environment

bash
python -m venv .venv
source .venv/bin/activate


On Windows PowerShell:

powershell
python -m venv .venv
.venv\Scripts\Activate.ps1


### 3. Install dependencies

If the project uses `pyproject.toml`:

bash
pip install -e .


To include development and test dependencies:

bash
pip install -e ".[dev]"


If a requirements file is provided instead:

bash
pip install -r requirements.txt


### 4. Configure environment variables

Copy the example environment file:

bash
cp .env.example .env


Example configuration:

dotenv
APP_NAME=FastAPI JWT Authentication
APP_ENV=development
DEBUG=true

DATABASE_URL=sqlite:///./app.db

JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30


For PostgreSQL:

dotenv
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/auth_db


Generate a secure JWT secret with:

bash
python -c "import secrets; print(secrets.token_urlsafe(64))"


Never commit production secrets or `.env` files to source control.

### 5. Apply database migrations

bash
alembic upgrade head


### 6. Start the application

bash
uvicorn app.main:app --reload


The API will be available at:

- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI schema: `http://127.0.0.1:8000/openapi.json`

## Authentication Flow

1. A user registers with an email or username and password.
2. The password is hashed before the user record is stored.
3. The user submits credentials to the login endpoint.
4. The server verifies the submitted password against the stored hash.
5. The server issues a signed JWT access token.
6. The client includes the token in subsequent requests:

http
Authorization: Bearer <access-token>


7. Protected endpoints validate the token signature, expiration, and subject before returning data.

## API Endpoints

Common authentication endpoints are listed below. Consult `/docs` for the exact request models and paths configured by the application.

| Method | Endpoint | Authentication | Description |
|---|---|---:|---|
| `POST` | `/auth/register` | No | Register a new user |
| `POST` | `/auth/login` | No | Authenticate and obtain an access token |
| `GET` | `/users/me` | Bearer token | Return the authenticated user |
| `GET` | `/health` | No | Return application health status |

### Register a user

bash
curl -X POST http://127.0.0.1:8000/auth/register \
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


### Log in

When the login endpoint uses OAuth2 form data:

bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=StrongPassword123!"


Example response:


{
  "access_token": "<jwt-token>",
  "token_type": "bearer"
}


### Access a protected endpoint

bash
curl http://127.0.0.1:8000/users/me \
  -H "Authorization: Bearer <jwt-token>"


## Database Migrations

Create a migration after changing a database model:

bash
alembic revision --autogenerate -m "describe model change"


Review the generated migration before applying it:

bash
alembic upgrade head


Roll back the latest migration:

bash
alembic downgrade -1


Display migration history:

bash
alembic history


## Running Tests

Run the complete test suite:

bash
pytest


Run tests with verbose output:

bash
pytest -v


Run authentication tests only:

bash
pytest tests/test_auth.py -v


Generate a coverage report:

bash
pytest --cov=app --cov-report=term-missing


Authentication tests should cover at least:

- Successful user registration
- Duplicate user rejection
- Password hashing and verification
- Successful login
- Invalid credential rejection
- Access with a valid token
- Missing-token rejection
- Invalid-token rejection
- Expired-token rejection

## Security Considerations

- Passwords are never stored or returned in plaintext.
- JWT secrets must be long, random, and managed through a secret store in production.
- Access tokens should have short expiration periods.
- Authentication errors should not reveal whether a specific account exists.
- HTTPS must be enabled in production.
- CORS should be restricted to trusted origins.
- Login and registration endpoints should be rate-limited.
- JWT payloads must not contain passwords, secrets, or sensitive personal data.
- Signing keys should be rotated according to the deployment security policy.
- Production databases should use encrypted connections and least-privilege credentials.

## Production Deployment

Before deploying:

1. Set `APP_ENV=production` and disable debug mode.
2. Store secrets in the deployment platform's secret manager.
3. Configure a production database.
4. Apply migrations as a controlled release step.
5. Serve the application behind an HTTPS reverse proxy or managed load balancer.
6. Configure trusted hosts and allowed CORS origins.
7. Add structured logging, monitoring, and alerting.
8. Run multiple workers where appropriate.

Example server command:

bash
gunicorn app.main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8000


Worker counts should be tuned based on CPU, memory, traffic, and database connection limits.

## Troubleshooting

### Migration cannot connect to the database

Verify that `DATABASE_URL` is valid, the database server is running, and the configured user has permission to modify the schema.

### Login always returns unauthorized

Confirm that the user exists, the password hashing configuration has not changed, and the login field matches the identifier expected by the API.

### Tokens are immediately rejected

Check `JWT_SECRET_KEY`, `JWT_ALGORITHM`, token expiration settings, and system clock synchronization across application instances.

### SQLite thread errors during tests

When using SQLite with FastAPI tests, configure the engine appropriately for the test environment and ensure all test sessions use the same test database setup.

## License

Add the project's license information here.