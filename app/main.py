import os
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles

from app.db import insert_file, get_file
from app.utils import ensure_dirs, unique_id, guess_mime, MAX_BYTES, STORAGE_DIR, now_iso

BASE_URL = os.getenv("BASE_URL", "http://localhost:8110")

ensure_dirs()

app = FastAPI(title="TechnIQStone Filehoster", docs_url=None, redoc_url=None)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "base_url": BASE_URL})

@app.get("/health", response_class=JSONResponse)
async def health():
    return {"status": "ok"}

@app.post("/upload", response_class=JSONResponse)
async def upload(file: UploadFile = File(...)):
    if file is None or not file.filename:
        raise HTTPException(status_code=400, detail="Keine Datei übergeben")

    fid = unique_id()
    dest_path = os.path.join(STORAGE_DIR, fid)

    mime = guess_mime(file.filename)

    size = 0
    try:
        with open(dest_path, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)  # 1 MB
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_BYTES:
                    out.close()
                    try:
                        os.remove(dest_path)
                    except FileNotFoundError:
                        pass
                    raise HTTPException(status_code=413, detail=f"Datei größer als erlaubte {MAX_BYTES} Bytes")
                out.write(chunk)
    finally:
        await file.close()

    insert_file(fid=fid, orig_name=file.filename, mime=mime, size=size, uploaded_at=now_iso())

    file_url = f"{BASE_URL}/files/{fid}"
    return {"id": fid, "url": file_url, "size": size, "mime": mime}

@app.get("/files/{fid}")
async def serve_file(fid: str):
    rec = get_file(fid)
    if not rec:
        raise HTTPException(status_code=404, detail="Datei nicht gefunden")

    path = os.path.join(STORAGE_DIR, fid)
    if not os.path.exists(path):
        raise HTTPException(status_code=410, detail="Datei existiert nicht mehr")

    headers = {"Content-Disposition": f"inline; filename=\"{rec['orig_name']}\""}
    return FileResponse(path, media_type=rec["mime"], headers=headers)
