import os
import sqlite3
from typing import Optional
from datetime import datetime, timezone
import pathlib

# Die DB liegt standardmäßig im STORAGE_DIR (z. B. /file)
STORAGE_DIR = os.getenv("STORAGE_DIR", "/file")
DEFAULT_DB = os.path.join(STORAGE_DIR, "metadata.sqlite3")
DB_PATH = os.getenv("DB_PATH", DEFAULT_DB)

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS files (
  id TEXT PRIMARY KEY,
  orig_name TEXT NOT NULL,
  mime TEXT NOT NULL,
  size INTEGER NOT NULL,
  uploaded_at TEXT NOT NULL,
  expires_at TEXT NULL
);
CREATE INDEX IF NOT EXISTS idx_files_expires_at ON files(expires_at);
"""

def get_conn() -> sqlite3.Connection:
    pathlib.Path(os.path.dirname(DB_PATH)).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def migrate():
    conn = get_conn()
    with conn:
        conn.executescript(SCHEMA)
        # Falls Tabelle schon existiert, aber Spalte fehlt:
        try:
            conn.execute("SELECT expires_at FROM files LIMIT 1;")
        except sqlite3.OperationalError:
            conn.execute("ALTER TABLE files ADD COLUMN expires_at TEXT;")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_files_expires_at ON files(expires_at);")
    conn.close()

def insert_file(fid: str, orig_name: str, mime: str, size: int, uploaded_at: str, expires_at: Optional[str]):
    conn = get_conn()
    with conn:
        conn.execute(
            "INSERT INTO files (id, orig_name, mime, size, uploaded_at, expires_at) VALUES (?, ?, ?, ?, ?, ?)",
            (fid, orig_name, mime, size, uploaded_at, expires_at),
        )
    conn.close()

def get_file(fid: str) -> Optional[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM files WHERE id = ?", (fid,))
    row = cur.fetchone()
    conn.close()
    return row

def purge_expired(now_iso: str) -> int:
    """Löscht abgelaufene Datensätze + zugehörige Dateien. Gibt Anzahl gelöschter Einträge zurück."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM files WHERE expires_at IS NOT NULL AND expires_at <= ?", (now_iso,))
    ids = [r["id"] for r in cur.fetchall()]
    deleted = 0
    for fid in ids:
        path = os.path.join(STORAGE_DIR, fid)
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        conn.execute("DELETE FROM files WHERE id = ?", (fid,))
        deleted += 1
    conn.commit()
    conn.close()
    return deleted
