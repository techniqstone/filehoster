import os
import mimetypes
import secrets
import string
from datetime import datetime, timezone

STORAGE_DIR = os.getenv("STORAGE_DIR", "/file")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "2048"))
MAX_BYTES = MAX_UPLOAD_MB * 1024 * 1024

ALPHABET = string.ascii_letters + string.digits

def ensure_dirs():
    os.makedirs(STORAGE_DIR, exist_ok=True)

def gen_id(length: int = 12) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))

def unique_id() -> str:
    while True:
        fid = gen_id(12)
        path = os.path.join(STORAGE_DIR, fid)
        if not os.path.exists(path):
            return fid

def guess_mime(filename: str, default: str = "application/octet-stream") -> str:
    mime, _ = mimetypes.guess_type(filename)
    return mime or default

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
