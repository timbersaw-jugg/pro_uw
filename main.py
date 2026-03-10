from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sqlite3
import json
import os
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "prouw.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            employee_id TEXT UNIQUE,
            user_id TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'user'
        );

        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            text TEXT,
            options TEXT,
            correct_answer TEXT,
            master_rationale TEXT,
            format TEXT,
            module INTEGER,
            time_limit INTEGER DEFAULT 60
        );

        CREATE TABLE IF NOT EXISTS test_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            end_time DATETIME,
            status TEXT DEFAULT 'in_progress',
            total_score REAL DEFAULT 0,
            total_explanation_score REAL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            question_id INTEGER,
            answer TEXT,
            explanation TEXT,
            ai_explanation_score REAL,
            admin_score REAL,
            admin_explanation_score REAL,
            FOREIGN KEY(session_id) REFERENCES test_sessions(id),
            FOREIGN KEY(question_id) REFERENCES questions(id)
        );

        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            details TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    """)
    
    # Seed Admin
    cursor.execute("SELECT * FROM users WHERE user_id = 'admin'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (first_name, last_name, employee_id, user_id, password, role) VALUES (?, ?, ?, ?, ?, ?)",
            ("System", "Admin", "ADMIN001", "admin", "mortgage2026", "admin")
        )
    conn.commit()
    conn.close()

init_db()

# --- Models ---
class UserRegister(BaseModel):
    firstName: str
    lastName: str
    employeeId: str
    userId: str
    password: str

class UserLogin(BaseModel):
    userId: str
    password: str

# --- API Routes ---

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.post("/api/register")
async def register(user: UserRegister):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (first_name, last_name, employee_id, user_id, password) VALUES (?, ?, ?, ?, ?)",
            (user.firstName, user.lastName, user.employeeId, user.userId, user.password)
        )
        conn.commit()
        return {"success": True, "userId": cursor.lastrowid}
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.post("/api/login")
async def login(data: UserLogin):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ? AND password = ?", (data.userId, data.password))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"success": True, "user": dict(user)}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/questions")
async def get_questions():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()
    conn.close()
    result = []
    for q in questions:
        q_dict = dict(q)
        if q_dict['options']:
            q_dict['options'] = json.loads(q_dict['options'])
        result.append(q_dict)
    return result

# ... (Other routes would be implemented similarly) ...

# Serve Vite static files in production
if os.path.exists("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="static")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if os.path.exists(os.path.join("dist", "index.html")):
        return FileResponse(os.path.join("dist", "index.html"))
    return {"error": "Frontend not built"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
