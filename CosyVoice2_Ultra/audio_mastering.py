"""Post-processing and mastering for generated speech."""
from __future__ import annotations
from pathlib import Path
import librosa
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt


def _compress(audio: np.ndarray, threshold: float = 0.35, ratio: float = 3.0) -> np.ndarray:
    """Apply a transparent static compressor."""
    sign = np.sign(audio); mag = np.abs(audio)
    over = mag > threshold
    mag[over] = threshold + (mag[over] - threshold) / ratio
    return sign * mag


def _speech_eq(audio: np.ndarray, sr: int) -> np.ndarray:
    """Apply gentle speech high-pass/low-pass filtering."""
    high = butter(2, 65, btype="highpass", fs=sr, output="sos")
    low = butter(2, min(10500, sr / 2 - 100), btype="lowpass", fs=sr, output="sos")
    return sosfilt(low, sosfilt(high, audio)).astype(np.float32)


def master_audio(audio: np.ndarray, sr: int, normalize: bool = True, remove_silence: bool = True, fade_ms: int = 20, noise_reduction: bool = False) -> np.ndarray:
    """Apply EQ, compression, silence trimming, fades, limiter, and soft clipping."""
    y = np.asarray(audio, dtype=np.float32).flatten()
    if not y.size:
        return y
    if remove_silence:
        y, _ = librosa.effects.trim(y, top_db=38)
    if noise_reduction:
        gate = max(float(np.sqrt(np.mean(y**2))) * 0.035, 0.0005)
        y[np.abs(y) < gate] *= 0.35
    y = _speech_eq(y, sr)
    y = _compress(y)
    if normalize:
        y = y / max(float(np.max(np.abs(y))), 1e-6) * 0.92
    n = min(int(sr * fade_ms / 1000), len(y) // 2)
    if n > 1:
        fade = np.linspace(0, 1, n, dtype=np.float32)
        y[:n] *= fade; y[-n:] *= fade[::-1]
    return np.tanh(y * 1.08).astype(np.float32)


def write_audio(path: str | Path, audio: np.ndarray, sr: int) -> str:
    """Write audio to disk in a format inferred from extension."""
    sf.write(str(path), audio, sr)
    return str(path)
