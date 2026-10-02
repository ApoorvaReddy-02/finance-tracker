# Personal Finance Tracker and Budgeting System
Full-stack budgeting app: add income/expenses, set category budgets, view monthly reports with over-budget alerts.

## Tech
Python, FastAPI, SQLite, HTML, CSS, JavaScript

## Run
```bash
pip install -r requirements.txt
uvicorn app:app --reload   # open http://127.0.0.1:8000
```
## API
`GET/POST /api/transactions`, `DELETE /api/transactions/{id}`, `PUT /api/budgets`, `GET /api/report/{YYYY-MM}`. Docs at `/docs`.
