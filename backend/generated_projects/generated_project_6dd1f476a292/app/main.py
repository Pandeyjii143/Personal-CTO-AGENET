import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Iterator

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


DB_PATH = Path(os.getenv('EXPENSES_DB_PATH', Path(__file__).with_name('expenses.db'))).expanduser()


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db() -> None:
    with get_db() as connection:
        connection.execute(
            '''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount > 0),
                category TEXT NOT NULL,
                date TEXT NOT NULL
            )
            '''
        )


class ExpenseInput(BaseModel):
    description: str = Field(min_length=1, max_length=200)
    amount: float = Field(gt=0)
    category: str = Field(min_length=1, max_length=100)
    date: date


class Expense(ExpenseInput):
    id: int


app = FastAPI(title='Personal Expense Tracker')
init_db()


@app.get('/', response_class=HTMLResponse)
def home() -> str:
    return HTML_PAGE


@app.get('/expenses', response_model=list[Expense])
def list_expenses() -> list[dict]:
    with get_db() as connection:
        rows = connection.execute(
            'SELECT id, description, amount, category, date FROM expenses ORDER BY date DESC, id DESC'
        ).fetchall()
    return [dict(row) for row in rows]


@app.post('/expenses', response_model=Expense, status_code=201)
def create_expense(expense: ExpenseInput) -> dict:
    with get_db() as connection:
        cursor = connection.execute(
            'INSERT INTO expenses (description, amount, category, date) VALUES (?, ?, ?, ?)',
            (expense.description.strip(), expense.amount, expense.category.strip(), expense.date.isoformat()),
        )
        row = connection.execute(
            'SELECT id, description, amount, category, date FROM expenses WHERE id = ?',
            (cursor.lastrowid,),
        ).fetchone()
    return dict(row)


@app.get('/expenses/{expense_id}', response_model=Expense)
def get_expense(expense_id: int) -> dict:
    with get_db() as connection:
        row = connection.execute(
            'SELECT id, description, amount, category, date FROM expenses WHERE id = ?',
            (expense_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail='Expense not found')
    return dict(row)


@app.put('/expenses/{expense_id}', response_model=Expense)
def update_expense(expense_id: int, expense: ExpenseInput) -> dict:
    with get_db() as connection:
        cursor = connection.execute(
            'UPDATE expenses SET description = ?, amount = ?, category = ?, date = ? WHERE id = ?',
            (
                expense.description.strip(),
                expense.amount,
                expense.category.strip(),
                expense.date.isoformat(),
                expense_id,
            ),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail='Expense not found')
        row = connection.execute(
            'SELECT id, description, amount, category, date FROM expenses WHERE id = ?',
            (expense_id,),
        ).fetchone()
    return dict(row)


@app.delete('/expenses/{expense_id}', status_code=204)
def delete_expense(expense_id: int) -> Response:
    with get_db() as connection:
        cursor = connection.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail='Expense not found')
    return Response(status_code=204)


HTML_PAGE = '''<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>Personal Expense Tracker</title>
  <style>
    body { font: 16px system-ui, sans-serif; max-width: 850px; margin: 2rem auto; padding: 0 1rem; color: #222; }
    form { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: .75rem; align-items: end; }
    label { display: grid; gap: .25rem; }
    input, button { font: inherit; padding: .5rem; }
    table { width: 100%; border-collapse: collapse; margin-top: 1.5rem; }
    th, td { padding: .6rem; border-bottom: 1px solid #ddd; text-align: left; }
    .actions { white-space: nowrap; }
    #message { min-height: 1.5em; color: #9b1c1c; }
  </style>
</head>
<body>
  <h1>Personal Expense Tracker</h1>
  <form id='expense-form'>
    <label>Description<input name='description' maxlength='200' required></label>
    <label>Amount<input name='amount' type='number' min='0.01' step='0.01' required></label>
    <label>Category<input name='category' maxlength='100' required></label>
    <label>Date<input name='date' type='date' required></label>
    <button type='submit'>Add expense</button>
  </form>
  <p id='message' role='status'></p>
  <table>
    <thead><tr><th>Date</th><th>Description</th><th>Category</th><th>Amount</th><th>Actions</th></tr></thead>
    <tbody id='expenses'></tbody>
  </table>
<script>
const form = document.querySelector('#expense-form');
const body = document.querySelector('#expenses');
const message = document.querySelector('#message');
form.elements.date.value = new Date().toISOString().slice(0, 10);

async function request(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Request failed');
  }
  return response.status === 204 ? null : response.json();
}

async function refresh() {
  try {
    const expenses = await request('/expenses');
    body.replaceChildren();
    for (const expense of expenses) {
      const row = document.createElement('tr');
      for (const value of [expense.date, expense.description, expense.category, Number(expense.amount).toFixed(2)]) {
        const cell = document.createElement('td');
        cell.textContent = value;
        row.appendChild(cell);
      }
      const actions = document.createElement('td');
      actions.className = 'actions';
      const edit = document.createElement('button');
      edit.textContent = 'Edit';
      edit.type = 'button';
      edit.addEventListener('click', () => editExpense(expense));
      const remove = document.createElement('button');
      remove.textContent = 'Delete';
      remove.type = 'button';
      remove.addEventListener('click', async () => {
        if (!confirm('Delete this expense?')) return;
        try { await request(`/expenses/${expense.id}`, { method: 'DELETE' }); await refresh(); }
        catch (error) { message.textContent = error.message; }
      });
      actions.append(edit, remove);
      row.appendChild(actions);
      body.appendChild(row);
    }
  } catch (error) {
    message.textContent = error.message;
  }
}

async function editExpense(expense) {
  const description = prompt('Description:', expense.description);
  if (description === null) return;
  const amount = prompt('Amount:', expense.amount);
  if (amount === null) return;
  const category = prompt('Category:', expense.category);
  if (category === null) return;
  const expenseDate = prompt('Date (YYYY-MM-DD):', expense.date);
  if (expenseDate === null) return;
  try {
    await request(`/expenses/${expense.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description, amount: Number(amount), category, date: expenseDate })
    });
    message.textContent = '';
    await refresh();
  } catch (error) {
    message.textContent = error.message;
  }
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  const values = new FormData(form);
  const expense = Object.fromEntries(values.entries());
  expense.amount = Number(expense.amount);
  try {
    await request('/expenses', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(expense)
    });
    form.reset();
    form.elements.date.value = new Date().toISOString().slice(0, 10);
    message.textContent = '';
    await refresh();
  } catch (error) {
    message.textContent = error.message;
  }
});

refresh();
</script>
</body>
</html>'''
