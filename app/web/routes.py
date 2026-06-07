import asyncio
from pathlib import Path
from uuid import uuid4

from celery.exceptions import CeleryError
from celery.result import AsyncResult
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from kombu.exceptions import KombuError
from starlette.requests import Request

from app.core.config import get_settings
from app.models.schemas import EmotionPreset, GenerationResponse
from app.services.audio_library import AudioLibrary
from app.services.local_jobs import local_jobs
from app.services.streaming import iter_audio_file
from app.tasks.celery_app import celery_app
from app.tasks.generation import generate_voice

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")


def _should_use_celery() -> bool:
    return get_settings().background_backend.lower() == "celery"


def _job_payload(
    text: str,
    voice_reference_path: str | None,
    emotion: EmotionPreset,
    emotional_intensity: float,
    stability: float,
) -> dict:
    return {
        "text": text,
        "voice_reference_path": voice_reference_path,
        "emotion": emotion.value,
        "emotional_intensity": emotional_intensity,
        "stability": stability,
    }


def _status_for_job(job_id: str) -> dict:
    local_status = local_jobs.get(job_id)
    if local_status:
        return local_status

    result = AsyncResult(job_id, app=celery_app)
    payload = result.info if isinstance(result.info, dict) else {}
    return {"job_id": job_id, "state": result.state, **payload}


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request, "assets": AudioLibrary().list_assets()})


@router.get("/favicon.ico")
def favicon() -> HTMLResponse:
    return HTMLResponse(status_code=204, content="")


@router.post("/api/voices")
async def upload_voice(file: UploadFile = File(...)) -> dict:
    settings = get_settings()
    suffix = Path(file.filename or "voice.wav").suffix or ".wav"
    voice_id = uuid4().hex
    destination = settings.voices_dir / f"{voice_id}{suffix}"
    size = 0
    with destination.open("wb") as handle:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > settings.max_upload_mb * 1024 * 1024:
                destination.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Voice sample is too large")
            handle.write(chunk)
    return {"voice_id": voice_id, "path": str(destination)}


@router.post("/api/generate", response_model=GenerationResponse)
async def create_generation(
    text: str = Form(...),
    voice_id: str | None = Form(default=None),
    emotion: EmotionPreset = Form(default=EmotionPreset.dramatic),
    emotional_intensity: float = Form(default=0.7),
    stability: float = Form(default=0.55),
) -> GenerationResponse:
    settings = get_settings()
    voice_reference_path = None
    if voice_id:
        matches = list(settings.voices_dir.glob(f"{voice_id}.*"))
        if not matches:
            raise HTTPException(status_code=404, detail="Voice reference not found")
        voice_reference_path = str(matches[0])

    payload = _job_payload(text, voice_reference_path, emotion, emotional_intensity, stability)

    if _should_use_celery():
        try:
            task = generate_voice.delay(payload)
            return GenerationResponse(job_id=task.id, status="queued")
        except (CeleryError, KombuError, OSError) as exc:
            job_id = local_jobs.submit(payload)
            return GenerationResponse(job_id=job_id, status=f"queued-local-fallback: {exc.__class__.__name__}")

    job_id = local_jobs.submit(payload)
    return GenerationResponse(job_id=job_id, status="queued-local")


@router.get("/api/jobs/{job_id}")
def job_status(job_id: str) -> dict:
    return _status_for_job(job_id)


@router.websocket("/ws/jobs/{job_id}")
async def job_progress(websocket: WebSocket, job_id: str) -> None:
    await websocket.accept()
    try:
        while True:
            status = _status_for_job(job_id)
            await websocket.send_json(status)
            if status.get("state") in {"SUCCESS", "FAILURE"}:
                break
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        return


@router.get("/api/audio")
def list_audio() -> dict:
    return {"assets": [asset.model_dump() for asset in AudioLibrary().list_assets()]}


@router.get("/api/audio/{audio_id}/stream")
async def stream_audio(audio_id: str) -> StreamingResponse:
    try:
        path = AudioLibrary().resolve_audio(audio_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Audio not found") from exc
    return StreamingResponse(iter_audio_file(path), media_type="audio/wav")
