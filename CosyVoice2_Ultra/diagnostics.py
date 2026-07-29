"""Diagnostics for generated and reference audio."""
from __future__ import annotations
from typing import Any
import numpy as np
from utils import nvidia_smi


def _vram_used() -> str:
    """Return current PyTorch VRAM allocation when available."""
    try:
        import torch
        if torch.cuda.is_available():
            return f"{torch.cuda.memory_allocated() / 1024**3:.2f} GB"
    except Exception:
        pass
    return "unavailable"


def audio_metrics(audio: np.ndarray, sr: int, generation_time: float, emotion: str) -> dict[str, Any]:
    """Compute user-facing generation diagnostics."""
    y = np.asarray(audio).flatten()
    peak = float(np.max(np.abs(y))) if y.size else 0.0
    rms = float(np.sqrt(np.mean(y**2))) if y.size else 0.0
    lufs = float(20 * np.log10(rms + 1e-9) - 0.691)
    return {
        "Emotion": emotion,
        "Generation Time": f"{generation_time:.2f}s",
        "Peak": f"{peak:.3f}",
        "LUFS": f"{lufs:.1f}",
        "Sample Rate": sr,
        "Duration": f"{len(y) / sr:.2f}s" if sr else "0.00s",
        "VRAM Used": _vram_used(),
        "GPU Telemetry": nvidia_smi(),
    }
