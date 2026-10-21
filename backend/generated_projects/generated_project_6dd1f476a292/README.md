# Personal Expense Tracker

A simple personal expense tracker built with **Python**, **FastAPI**, and **SQLite**. It provides a basic HTML interface and REST API for managing expenses.

## Features

- Add expenses with a description, amount, category, and date
- Edit existing expenses
- Delete expenses
- List all recorded expenses
- Validate that expense amounts are greater than zero
- Persist data in a local SQLite database
- Use a basic browser-based HTML interface
- Access interactive OpenAPI documentation
- Run automated tests with `pytest`

## Technology Stack

- Python 3.10+
- FastAPI
- SQLite
- SQLAlchemy
- Jinja2
- Uvicorn
- Pytest

## Project Structure

text
.
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   ├── templates/
│   │   ├── index.html
│   │   └── edit_expense.html
│   └── static/
│       └── styles.css
├── tests/
│   └── test_expenses.py
├── requirements.txt
└── README.md


> The exact structure may vary slightly depending on the implementation.

## Getting Started

### 1. Clone the repository

bash
git clone <repository-url>
cd <repository-directory>


### 2. Create a virtual environment

bash
python -m venv .venv


Activate it on macOS or Linux:

bash
source .venv/bin/activate


Activate it on Windows PowerShell:

powershell
.venv\Scripts\Activate.ps1


### 3. Install dependencies

bash
pip install -r requirements.txt


If a requirements file has not yet been created, install the primary dependencies directly:

bash
pip install fastapi uvicorn sqlalchemy jinja2 python-multipart pytest httpx


### 4. Start the application

bash
uvicorn app.main:app --reload


The application will be available at:

- HTML interface: <http://127.0.0.1:8000/>
- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

The SQLite database is created automatically when the application starts.

## Expense Data

Each expense contains the following fields:

| Field | Type | Description |
|---|---|---|
| `id` | Integer | Unique expense identifier |
| `description` | String | Description of the expense |
| `amount` | Number | Positive monetary amount |
| `category` | String | Expense category |
| `date` | Date | Date on which the expense occurred |

Example:


{
  "id": 1,
  "description": "Lunch",
  "amount": 14.5,
  "category": "Food",
  "date": "2025-01-15"
}


Amounts must be greater than zero. Invalid amounts are rejected with a validation error.

## API Endpoints

A typical REST API exposes the following operations:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/expenses` | List all expenses |
| `POST` | `/expenses` | Create an expense |
| `GET` | `/expenses/{expense_id}` | Retrieve one expense |
| `PUT` | `/expenses/{expense_id}` | Update an expense |
| `DELETE` | `/expenses/{expense_id}` | Delete an expense |

### Create an expense

bash
curl -X POST http://127.0.0.1:8000/expenses \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Groceries",
    "amount": 52.75,
    "category": "Food",
    "date": "2025-01-15"
  }'


### List expenses

bash
curl http://127.0.0.1:8000/expenses


### Update an expense

bash
curl -X PUT http://127.0.0.1:8000/expenses/1 \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Weekly groceries",
    "amount": 60.25,
    "category": "Food",
    "date": "2025-01-15"
  }'


### Delete an expense

bash
curl -X DELETE http://127.0.0.1:8000/expenses/1


## HTML Interface

Open <http://127.0.0.1:8000/> in a browser to use the basic HTML interface. From there, users can:

1. View recorded expenses
2. Add a new expense
3. Edit an existing expense
4. Delete an expense

The interface uses server-rendered HTML templates and requires no separate frontend build process.

## Running Tests

Run the complete test suite from the project root:

bash
pytest


For verbose output:

bash
pytest -v


The tests should cover at least:

- Creating a valid expense
- Rejecting zero or negative amounts
- Listing expenses
- Updating an expense
- Deleting an expense
- Handling an unknown expense ID

## Configuration

By default, the application uses a local SQLite database. A typical database URL is:

text
sqlite:///./expenses.db


For test isolation, configure the test suite to use a separate temporary SQLite database or an in-memory database.

Do not commit local database files. Add them to `.gitignore`:

gitignore
.venv/
__pycache__/
.pytest_cache/
*.py[cod]
*.db
.env


## Validation and Error Handling

- `amount` must be greater than `0`
- Required fields must be provided
- `date` must use a valid ISO date such as `2025-01-15`
- Requests for unknown expenses should return `404 Not Found`
- Invalid request bodies should return FastAPI's standard `422 Unprocessable Entity` response

## Development Notes

- Use decimal-compatible database types for monetary values where practical; avoid relying on binary floating-point arithmetic for financial calculations.
- Keep database sessions scoped to individual requests.
- Use a separate database during automated testing.
- Review generated migration requirements before changing the data model in a production environment.

## License

This project is available for personal and educational use. Add an appropriate license file before distributing or publishing it.
