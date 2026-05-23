from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.services.media_service import MediaToolError, download_video_file, extract_mp3, fetch_video_metadata, video_to_gif

router = APIRouter()


@router.post('/metadata')
async def media_metadata(url: str = Form(...)) -> dict:
    try:
        return await fetch_video_metadata(url)
    except MediaToolError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/download')
async def media_download(url: str = Form(...), format_id: str | None = Form(default=None)) -> StreamingResponse:
    try:
        filename, content = await download_video_file(url, format_id)
        return StreamingResponse(iter([content]), media_type='application/octet-stream', headers={'Content-Disposition': f'attachment; filename="{filename}"'})
    except MediaToolError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/video-to-gif')
async def convert_video_to_gif(file: UploadFile = File(...), fps: int = Form(default=12)) -> StreamingResponse:
    try:
        content = await video_to_gif(await file.read(), fps=fps)
        return StreamingResponse(iter([content]), media_type='image/gif', headers={'Content-Disposition': 'attachment; filename="converted.gif"'})
    except MediaToolError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/extract-audio')
async def extract_audio(file: UploadFile = File(...), bitrate: str = Form(default='192k')) -> StreamingResponse:
    try:
        content = await extract_mp3(await file.read(), bitrate=bitrate)
        return StreamingResponse(iter([content]), media_type='audio/mpeg', headers={'Content-Disposition': 'attachment; filename="audio.mp3"'})
    except MediaToolError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
