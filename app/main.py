import os
import asyncio
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles

from app.db import insert_file, get_file, migrate, purge_expired
from app.utils import ensure_dirs, unique_id, guess_mime, MAX_BYTES, STORAGE_DIR, now_iso

BASE_URL = os.getenv("BASE_URL", "http://localhost:8110")

ensure_dirs()
migrate()

app = FastAPI(title="TechnIQStone Filehoster", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

EXPIRY_CHOICES = {
    "1m": timedelta(minutes=1),
    "1h": timedelta(hours=1),
    "1d": timedelta(days=1),
    "1w": timedelta(weeks=1),
    "1y": timedelta(days=365),
    "forever": None,
}

@app.on_event("startup")
async def _startup():
    # kleiner Hintergrund-Cleaner (stündlich)
    async def cleaner():
        while True:
            purge_expired(now_iso())
            await asyncio.sleep(3600)
    asyncio.create_task(cleaner())

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload(file: UploadFile = File(...), expiry: str = Form("forever")):
    if expiry not in EXPIRY_CHOICES:
        raise HTTPException(status_code=400, detail="Ungültige Ablaufzeit")

    fid = unique_id()
    dest_path = os.path.join(STORAGE_DIR, fid)

    # Stream-Speicher (RAM-schonend) + Größenlimit
    size = 0
    try:
        with open(dest_path, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)  # 1 MiB
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_BYTES:
                    raise HTTPException(status_code=413, detail="Datei zu groß")
                out.write(chunk)
    except Exception:
        # Aufräumen bei Abbruch/Fall
        if os.path.exists(dest_path):
            try: os.remove(dest_path)
            except: pass
        raise

    mime = guess_mime(file.filename)
    now = datetime.now(timezone.utc)
    td = EXPIRY_CHOICES[expiry]
    expires_at = (now + td).isoformat() if td else None

    insert_file(
        fid=fid,
        orig_name=file.filename,
        mime=mime,
        size=size,
        uploaded_at=now.isoformat(),
        expires_at=expires_at,
    )

    file_url = f"{BASE_URL}/files/{fid}"
    return {"id": fid, "url": file_url, "size": size, "mime": mime, "expires_at": expires_at}

@app.get("/files/{fid}")
async def serve_file(fid: str):
    rec = get_file(fid)
    if not rec:
        raise HTTPException(status_code=404, detail="Datei nicht gefunden")

    # Ablauf prüfen
    if rec["expires_at"]:
        try:
            if datetime.fromisoformat(rec["expires_at"]) <= datetime.now(timezone.utc):
                # Abgelaufen -> aufräumen & 410
                purge_expired(now_iso())
                raise HTTPException(status_code=410, detail="Link abgelaufen")
        except ValueError:
            # falls altes Format – ignorieren
            pass

    path = os.path.join(STORAGE_DIR, fid)
    if not os.path.exists(path):
        raise HTTPException(status_code=410, detail="Datei existiert nicht mehr")

    headers = {"Content-Disposition": f'inline; filename="{rec["orig_name"]}"'}
    return FileResponse(path, media_type=rec["mime"], headers=headers)

# optional manuelles Aufräumen
@app.post("/admin/purge")
async def admin_purge():
    n = purge_expired(now_iso())
    return {"deleted": n}
