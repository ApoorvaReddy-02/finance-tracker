import sqlite3
from datetime import date
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Literal

DB = "finance.db"
app = FastAPI(title="Personal Finance Tracker")

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

with db() as c:
    c.execute("""CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT CHECK(kind IN ('income','expense')) NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL CHECK(amount > 0),
        note TEXT DEFAULT '',
        tx_date TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS budgets(
        category TEXT PRIMARY KEY, monthly_limit REAL NOT NULL)""")

class Tx(BaseModel):
    kind: Literal["income", "expense"]
    category: str = Field(min_length=1, max_length=40)
    amount: float = Field(gt=0)
    note: str = ""
    tx_date: str = Field(default_factory=lambda: date.today().isoformat())

class Budget(BaseModel):
    category: str
    monthly_limit: float = Field(gt=0)

@app.get("/api/transactions")
def list_tx(month: str | None = None):
    q, a = "SELECT * FROM transactions", []
    if month:
        q += " WHERE substr(tx_date,1,7)=?"; a.append(month)
    with db() as c:
        return [dict(r) for r in c.execute(q + " ORDER BY tx_date DESC, id DESC", a)]

@app.post("/api/transactions", status_code=201)
def add_tx(t: Tx):
    with db() as c:
        cur = c.execute("INSERT INTO transactions(kind,category,amount,note,tx_date) VALUES(?,?,?,?,?)",
                        (t.kind, t.category.strip().title(), t.amount, t.note, t.tx_date))
    return {"id": cur.lastrowid}

@app.delete("/api/transactions/{tid}")
def del_tx(tid: int):
    with db() as c:
        if c.execute("DELETE FROM transactions WHERE id=?", (tid,)).rowcount == 0:
            raise HTTPException(404, "Not found")
    return {"deleted": tid}

@app.put("/api/budgets")
def set_budget(b: Budget):
    with db() as c:
        c.execute("INSERT INTO budgets VALUES(?,?) ON CONFLICT(category) DO UPDATE SET monthly_limit=excluded.monthly_limit",
                  (b.category.strip().title(), b.monthly_limit))
    return {"ok": True}

@app.get("/api/report/{month}")
def report(month: str):
    """Monthly report: totals, spending by category, budget status."""
    with db() as c:
        tot = {r["kind"]: r["s"] for r in c.execute(
            "SELECT kind, SUM(amount) s FROM transactions WHERE substr(tx_date,1,7)=? GROUP BY kind", (month,))}
        cats = [dict(r) for r in c.execute(
            """SELECT t.category, SUM(t.amount) spent, b.monthly_limit
               FROM transactions t LEFT JOIN budgets b ON b.category=t.category
               WHERE t.kind='expense' AND substr(t.tx_date,1,7)=? GROUP BY t.category ORDER BY spent DESC""", (month,))]
    income, expense = tot.get("income", 0), tot.get("expense", 0)
    for r in cats:
        r["over_budget"] = bool(r["monthly_limit"] and r["spent"] > r["monthly_limit"])
    return {"month": month, "income": income, "expense": expense, "savings": income - expense, "categories": cats}

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("static/index.html")
