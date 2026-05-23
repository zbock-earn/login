from __future__ import annotations

import random
import subprocess
from pathlib import Path
from urllib.parse import quote_plus

import yt_dlp
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from yt_dlp.utils import DownloadError

from app.services.media_service import MediaToolError, extract_mp3, video_to_gif

router = APIRouter()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/123.0 Safari/537.36",
]


def ensure_ytdlp_updated() -> None:
    subprocess.run(["python", "-m", "pip", "install", "--upgrade", "yt-dlp"], check=False, capture_output=True)


def build_fallback_url(url: str) -> str:
    u = url.lower()
    encoded = quote_plus(url)
    if "tiktok.com" in u:
        return f"https://www.tikwm.com/video/media/hdplay/{encoded}"
    if "instagram.com" in u:
        return f"https://snapinsta.app/?url={encoded}"
    if "youtube.com" in u or "youtu.be" in u:
        return f"https://cobalt.tools/?u={encoded}"
    return url


def _ydl_opts(download: bool = False, outtmpl: str | None = None, format_id: str | None = None) -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": not download,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "restrictfilenames": True,
        "http_headers": {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }
    cookies = Path("/workspace/login/cookies.txt")
    if cookies.exists():
        opts["cookiefile"] = str(cookies)
    if download:
        opts.update({
            "outtmpl": outtmpl,
            "format": format_id or "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
        })
    return opts


def _translate_error(exc: Exception) -> HTTPException:
    msg = str(exc)
    if "403" in msg or "Sign in to confirm" in msg or "blocked" in msg.lower():
        return HTTPException(status_code=403, detail="Platform blocked automated access from current IP.")
    if "Video unavailable" in msg:
        return HTTPException(status_code=400, detail="Video unavailable or removed.")
    return HTTPException(status_code=400, detail=f"Media processing failed: {msg}")


@router.post('/metadata')
async def media_metadata(url: str = Form(...)) -> dict:
    ensure_ytdlp_updated()
    try:
        with yt_dlp.YoutubeDL(_ydl_opts(download=False)) as ydl:
            info = ydl.extract_info(url, download=False)
        formats = [{"format_id": f.get("format_id"), "ext": f.get("ext"), "resolution": f.get("resolution") or f"{f.get('height', 'NA')}p"} for f in info.get("formats", []) if f.get("vcodec") != "none"]
        return {"title": info.get("title"), "duration": info.get("duration"), "thumbnail": info.get("thumbnail"), "formats": formats[:25], "fallback_url": build_fallback_url(url)}
    except Exception:
        return {"title": "Fallback Mode", "duration": None, "thumbnail": None, "formats": [], "fallback_url": build_fallback_url(url), "warning": "Extractor failed. Using fallback download page."}


@router.post('/download')
async def media_download(url: str = Form(...), format_id: str | None = Form(default=None)):
    ensure_ytdlp_updated()
    from tempfile import TemporaryDirectory
    try:
        with TemporaryDirectory() as tmp:
            tmpl = f"{tmp}/%(title).80s.%(ext)s"
            with yt_dlp.YoutubeDL(_ydl_opts(download=True, outtmpl=tmpl, format_id=format_id)) as ydl:
                info = ydl.extract_info(url, download=True)
                fp = Path(ydl.prepare_filename(info))
                if not fp.exists():
                    matches = list(Path(tmp).glob("*"))
                    fp = max(matches, key=lambda p: p.stat().st_mtime)
                content = fp.read_bytes()
                return StreamingResponse(iter([content]), media_type='application/octet-stream', headers={'Content-Disposition': f'attachment; filename="{fp.name}"'})
    except Exception:
        return JSONResponse(status_code=202, content={"fallback_url": build_fallback_url(url), "message": "Direct download blocked for this IP. Open fallback URL."})


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
