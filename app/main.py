from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import MAX_CONTENT_LENGTH, OUTPUT_DIR, RETENTION_TTL_SECONDS, TMP_DIR
from app.converters.engine import convert_file
from app.utils.matrix import FORMAT_MATRIX, get_allowed_targets

app = FastAPI(title="ConvertOmni", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
app.mount("/storage", StaticFiles(directory="storage"), name="storage")


def cleanup_paths(*paths: Path) -> None:
    for p in paths:
        try:
            if p.is_file():
                p.unlink(missing_ok=True)
        except Exception:
            pass


@app.middleware("http")
async def limit_payload(request: Request, call_next):
    length = request.headers.get("content-length")
    if length and int(length) > MAX_CONTENT_LENGTH:
        return JSONResponse({"detail": "Payload too large (max 500MB)."}, status_code=413)
    return await call_next(request)


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "ConvertOmni"}


@app.get("/api/formats")
async def formats():
    return FORMAT_MATRIX




@app.get("/api/capabilities")
async def capabilities():
    total_extensions = sum(len(v["extensions"]) for v in FORMAT_MATRIX.values())
    total_targets = sum(len(v["targets"]) for v in FORMAT_MATRIX.values())
    return {
        "categories": list(FORMAT_MATRIX.keys()),
        "total_extensions": total_extensions,
        "total_targets": total_targets,
        "max_upload_mb": MAX_CONTENT_LENGTH // (1024 * 1024),
        "retention_ttl_seconds": RETENTION_TTL_SECONDS,
    }

@app.post("/api/convert")
async def convert(background_tasks: BackgroundTasks, file: UploadFile = File(...), target: str = Form(...), options: str = Form("{}")):
    allowed = get_allowed_targets(file.filename)
    if target.lower() not in allowed:
        raise HTTPException(status_code=400, detail=f"Target '{target}' is not valid for '{file.filename}'.")

    start = time.perf_counter()
    request_id = uuid.uuid4().hex
    src_path = TMP_DIR / f"{request_id}_{Path(file.filename).name}"
    out_name = f"{Path(file.filename).stem}.{target.lower()}"
    out_path = OUTPUT_DIR / f"{request_id}_{out_name}"

    data = await file.read()
    src_path.write_bytes(data)

    try:
        opts = json.loads(options) if options else {}
        converted = convert_file(src_path, out_path, target.lower(), opts)
    except Exception as exc:
        cleanup_paths(src_path, out_path)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {exc}") from exc

    elapsed = round(time.perf_counter() - start, 3)
    size_mb = round(converted.stat().st_size / (1024 * 1024), 3)

    headers = {
        "X-Convert-Time-Seconds": str(elapsed),
        "X-Output-Size-MB": str(size_mb),
        "X-Retention-TTL": str(RETENTION_TTL_SECONDS),
    }

    background_tasks.add_task(cleanup_paths, src_path, converted)
    return FileResponse(path=converted, filename=out_name, media_type="application/octet-stream", headers=headers)
