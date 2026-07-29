"""Model download cache management for CosyVoice2 assets."""
from __future__ import annotations
from pathlib import Path
from huggingface_hub import snapshot_download
from settings import MODEL

_REQUIRED_MARKERS = ("cosyvoice.yaml", "configuration.json", "README.md")


def ensure_model() -> Path:
    """Download CosyVoice2 once and return the local cached model path."""
    MODEL.local_dir.mkdir(parents=True, exist_ok=True)
    if any((MODEL.local_dir / marker).exists() for marker in _REQUIRED_MARKERS) and any(MODEL.local_dir.rglob("*token*")):
        return MODEL.local_dir
    snapshot_download(
        repo_id=MODEL.repo_id,
        local_dir=str(MODEL.local_dir),
        local_dir_use_symlinks=False,
        resume_download=True,
        allow_patterns=["*"],
    )
    return MODEL.local_dir
