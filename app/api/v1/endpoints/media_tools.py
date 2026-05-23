from __future__ import annotations

import json
import os
import random
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

import yt_dlp
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from app.services.media_service import MediaToolError, extract_mp3, video_to_gif

router = APIRouter()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/123.0 Safari/537.36",
]


def ensure_ytdlp_updated() -> None:
    subprocess.run(["python", "-m", "pip", "install", "--upgrade", "yt-dlp"], check=False, capture_output=True)


def _fetch_json(url: str) -> dict:
    req = Request(url, headers={"User-Agent": random.choice(USER_AGENTS)})
    with urlopen(req, timeout=12) as resp:  # nosec B310
        return json.loads(resp.read().decode("utf-8", errors="ignore"))


def tiktok_direct(url: str) -> dict | None:
    try:
        data = _fetch_json(f"https://www.tikwm.com/api/?url={quote_plus(url)}")
        d = data.get("data") or {}
        play = d.get("play") or d.get("wmplay")
        if play:
            return {"title": d.get("title") or "TikTok video", "direct_url": play}
    except Exception:
        return None
    return None


def youtube_piped_fallback(url: str) -> dict | None:
    try:
        vid = url.split("v=")[-1].split("&")[0] if "v=" in url else url.rsplit("/", 1)[-1]
        data = _fetch_json(f"https://piped.video/api/v1/streams/{vid}")
        streams = data.get("videoStreams") or []
        if streams:
            best = streams[0]
            return {"title": data.get("title") or "YouTube video", "direct_url": best.get("url")}
    except Exception:
        return None
    return None


def instagram_direct_fallback(url: str) -> dict | None:
    try:
        direct = url.replace("https://www.instagram.com", "https://www.ddinstagram.com")
        return {"title": "Instagram Reel", "direct_url": direct}
    except Exception:
        return None


def build_fallback_url(url: str) -> str:
    u = url.lower()
    if "tiktok.com" in u:
        return f"https://www.tikwm.com/?url={quote_plus(url)}"
    if "instagram.com" in u:
        return url.replace("https://www.instagram.com", "https://www.ddinstagram.com")
    if "youtube.com" in u or "youtu.be" in u:
        return f"https://piped.video/watch?v={quote_plus(url)}"
    return url


def _resolve_cookiefile() -> str | None:
    file_path = Path("/workspace/login/cookies.txt")
    if file_path.exists():
        return str(file_path)
    env_path = os.getenv("YT_COOKIES_FILE")
    if env_path and Path(env_path).exists():
        return env_path
    return None


def _ydl_opts(download: bool = False, outtmpl: str | None = None, format_id: str | None = None) -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "best",
        "extract_flat": False,
        "skip_download": not download,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "ignoreerrors": False,
        "restrictfilenames": True,
        "retries": 3,
        "socket_timeout": 20,
        "extractor_retries": 3,
        "http_headers": {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        },
        "extractor_args": {
            "youtube": {"player_client": ["android", "web", "mweb"]},
        },
    }
    cookiefile = _resolve_cookiefile()
    if cookiefile:
        opts["cookiefile"] = cookiefile
    if download:
        opts.update({"outtmpl": outtmpl, "format": format_id or "bestvideo+bestaudio/best", "merge_output_format": "mp4"})
    return opts


def _youtube_auth_hint() -> str:
    return "YouTube blocked this server IP/session. Add valid cookies.txt (or YT_COOKIES_FILE env) and retry."


@router.post('/metadata')
async def media_metadata(url: str = Form(...)) -> dict:
    ensure_ytdlp_updated()
    try:
        with yt_dlp.YoutubeDL(_ydl_opts(download=False)) as ydl:
            info = ydl.extract_info(url, download=False)
        formats = [{"format_id": f.get("format_id"), "ext": f.get("ext"), "resolution": f.get("resolution") or f"{f.get('height', 'NA')}p"} for f in info.get("formats", []) if f.get("vcodec") != "none"]
        return {"title": info.get("title"), "duration": info.get("duration"), "thumbnail": info.get("thumbnail"), "formats": formats[:25]}
    except Exception as exc:
        low = str(exc).lower()
        if "youtube" in url.lower() and ("sign in to confirm" in low or "not a bot" in low):
            yt = youtube_piped_fallback(url)
            if yt and yt.get("direct_url"):
                return {"title": yt["title"], "duration": None, "formats": [{"format_id": "direct", "ext": "mp4", "resolution": "Auto"}], "warning": _youtube_auth_hint()}
            raise HTTPException(status_code=503, detail=_youtube_auth_hint()) from exc

        tk = tiktok_direct(url) if "tiktok.com" in url.lower() else None
        if tk:
            return {"title": tk["title"], "duration": None, "formats": [{"format_id": "direct", "ext": "mp4", "resolution": "HD"}], "warning": "Extractor blocked. Using direct TikTok fallback stream."}
        ig = instagram_direct_fallback(url) if "instagram.com" in url.lower() else None
        if ig:
            return {"title": ig["title"], "duration": None, "formats": [{"format_id": "direct", "ext": "mp4", "resolution": "Auto"}], "warning": "Extractor blocked. Using Instagram fallback mirror."}
        raise HTTPException(status_code=503, detail="Extractor blocked from current server IP. Please retry.") from exc


@router.post('/download')
async def media_download(url: str = Form(...), format_id: str | None = Form(default=None)):
    ensure_ytdlp_updated()
    try:
        with TemporaryDirectory() as tmp:
            tmpl = f"{tmp}/%(title).80s.%(ext)s"
            with yt_dlp.YoutubeDL(_ydl_opts(download=True, outtmpl=tmpl, format_id=format_id)) as ydl:
                info = ydl.extract_info(url, download=True)
                fp = Path(ydl.prepare_filename(info))
                if not fp.exists():
                    fp = max(Path(tmp).glob("*"), key=lambda p: p.stat().st_mtime)
                return StreamingResponse(iter([fp.read_bytes()]), media_type='application/octet-stream', headers={'Content-Disposition': f'attachment; filename="{fp.name}"'})
    except Exception as exc:
        low = str(exc).lower()
        if "youtube" in url.lower() and ("sign in to confirm" in low or "not a bot" in low):
            yt = youtube_piped_fallback(url)
            if yt and yt.get("direct_url"):
                return JSONResponse(status_code=202, content={"fallback_url": yt["direct_url"], "message": _youtube_auth_hint()})
            raise HTTPException(status_code=503, detail=_youtube_auth_hint()) from exc

        tk = tiktok_direct(url) if "tiktok.com" in url.lower() else None
        yt = youtube_piped_fallback(url) if ("youtube.com" in url.lower() or "youtu.be" in url.lower()) else None
        ig = instagram_direct_fallback(url) if "instagram.com" in url.lower() else None
        fallback = tk["direct_url"] if tk else (yt["direct_url"] if yt and yt.get("direct_url") else (ig["direct_url"] if ig and ig.get("direct_url") else build_fallback_url(url)))
        return JSONResponse(status_code=202, content={"fallback_url": fallback, "message": "Direct server download blocked; opening fallback stream."})


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
