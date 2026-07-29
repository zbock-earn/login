"""Export generated audio to common production formats."""
from __future__ import annotations
from pathlib import Path
import soundfile as sf
from pydub import AudioSegment

def export_audio(wav_path: str, fmt: str) -> str:
    """Export a WAV master to WAV, MP3, FLAC, or OGG."""
    fmt = fmt.lower(); src = Path(wav_path); dst = src.with_suffix(f".{fmt}")
    if fmt == "wav": return str(src)
    if fmt in {"flac", "ogg"}:
        data, sr = sf.read(src); sf.write(dst, data, sr, format=fmt.upper()); return str(dst)
    if fmt == "mp3":
        AudioSegment.from_wav(src).export(dst, format="mp3", bitrate="192k"); return str(dst)
    raise ValueError(f"Unsupported export format: {fmt}")
