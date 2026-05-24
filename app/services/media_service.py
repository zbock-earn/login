from __future__ import annotations

import os
import tempfile
from pathlib import Path

import yt_dlp
from moviepy import VideoFileClip


class MediaToolError(Exception):
    pass


def _safe_info(url: str) -> dict:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


async def fetch_video_metadata(url: str) -> dict:
    try:
        info = _safe_info(url)
        formats = []
        for fmt in info.get("formats", []):
            if fmt.get("vcodec") != "none":
                formats.append(
                    {
                        "format_id": fmt.get("format_id"),
                        "ext": fmt.get("ext"),
                        "resolution": fmt.get("resolution") or f"{fmt.get('height', 'NA')}p",
                        "filesize": fmt.get("filesize") or 0,
                    }
                )
        return {
            "title": info.get("title"),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "formats": formats[:20],
        }
    except Exception as exc:
        raise MediaToolError(f"Unable to fetch metadata: {exc}") from exc


async def download_video_file(url: str, format_id: str | None = None) -> tuple[str, bytes]:
    with tempfile.TemporaryDirectory() as tmpdir:
        outtmpl = str(Path(tmpdir) / "%(title).80s.%(ext)s")
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "outtmpl": outtmpl,
            "format": format_id or "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = Path(ydl.prepare_filename(info))
                if file_path.suffix.lower() not in {".mp4", ".webm", ".mkv"}:
                    candidates = list(Path(tmpdir).glob("*"))
                    file_path = max(candidates, key=lambda p: p.stat().st_mtime)
                return file_path.name, file_path.read_bytes()
        except Exception as exc:
            raise MediaToolError(f"Download failed: {exc}") from exc


async def video_to_gif(video_bytes: bytes, fps: int = 12) -> bytes:
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.mp4"
        out = Path(tmpdir) / "output.gif"
        src.write_bytes(video_bytes)
        try:
            clip = VideoFileClip(str(src))
            clip.write_gif(str(out), fps=fps)
            clip.close()
            return out.read_bytes()
        except Exception as exc:
            raise MediaToolError(f"GIF conversion failed: {exc}") from exc


async def extract_mp3(video_bytes: bytes, bitrate: str = "192k") -> bytes:
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.mp4"
        out = Path(tmpdir) / "audio.mp3"
        src.write_bytes(video_bytes)
        try:
            clip = VideoFileClip(str(src))
            if clip.audio is None:
                raise MediaToolError("No audio stream found")
            clip.audio.write_audiofile(str(out), bitrate=bitrate, logger=None)
            clip.close()
            return out.read_bytes()
        except Exception as exc:
            raise MediaToolError(f"MP3 extraction failed: {exc}") from exc
