import os
import sqlite3
from typing import Optional

DB_PATH = os.getenv("DB_PATH", "/app/data/app.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
  id TEXT PRIMARY KEY,
  orig_name TEXT NOT NULL,
  mime TEXT NOT NULL,
  size INTEGER NOT NULL,
  uploaded_at TEXT NOT NULL
);
"""

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

_conn = get_conn()
_conn.execute(SCHEMA)
_conn.commit()
_conn.close()

def insert_file(fid: str, orig_name: str, mime: str, size: int, uploaded_at: str) -> None:
    conn = get_conn()
    with conn:
        conn.execute(
            "INSERT INTO files (id, orig_name, mime, size, uploaded_at) VALUES (?, ?, ?, ?, ?)",
            (fid, orig_name, mime, size, uploaded_at),
        )
    conn.close()

def get_file(fid: str) -> Optional[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM files WHERE id = ?", (fid,))
    row = cur.fetchone()
    conn.close()
    return row
