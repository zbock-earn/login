"""Reference voice quality analysis, caching, trimming, consistency, and ranking."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import hashlib
import librosa
import numpy as np
import soundfile as sf
from settings import CACHE_DIR

@dataclass
class ReferenceReport:
    """Quality metrics for a reference recording."""
    path: str
    original_path: str
    duration: float
    sample_rate: int
    rms: float
    peak: float
    silence_ratio: float
    noise_score: float
    echo_score: float
    speaker_consistency: float
    quality_score: float


def _hash_file(path: str) -> str:
    """Return a stable short hash for reference caching."""
    h = hashlib.sha256(); h.update(Path(path).read_bytes()); return h.hexdigest()[:16]


def _embedding(audio: np.ndarray, sr: int) -> np.ndarray:
    """Compute a lightweight speaker/prosody embedding from MFCC statistics."""
    mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=20)
    return np.concatenate([mfcc.mean(axis=1), mfcc.std(axis=1)]).astype(np.float32)


def _echo_score(audio: np.ndarray, sr: int) -> float:
    """Estimate echo/reverberation using late autocorrelation energy."""
    if len(audio) < sr // 2:
        return 0.0
    corr = np.correlate(audio[: min(len(audio), sr * 3)], audio[: min(len(audio), sr * 3)], mode="full")
    corr = corr[len(corr) // 2:]
    if corr[0] == 0:
        return 0.0
    late = corr[int(sr * 0.05): int(sr * 0.35)] / corr[0]
    return float(np.clip(np.max(np.abs(late)) * 3.0, 0, 1)) if late.size else 0.0


def analyze_reference(path: str) -> ReferenceReport:
    """Analyze one reference, write a normalized cached WAV, and return metrics."""
    audio, sr = librosa.load(path, sr=24000, mono=True)
    if audio.size == 0:
        raise ValueError("Reference audio is empty")
    rms = float(np.sqrt(np.mean(audio**2)))
    peak = float(np.max(np.abs(audio)))
    silence_ratio = float(np.mean(np.abs(audio) < max(0.004, rms * 0.22)))
    head = audio[: min(len(audio), sr)]
    noise_score = float(np.clip(np.median(np.abs(head)) / (rms + 1e-6), 0, 1))
    echo = _echo_score(audio, sr)
    duration = float(len(audio) / sr)
    trimmed, _ = librosa.effects.trim(audio, top_db=35)
    if trimmed.size:
        audio = trimmed
    audio = audio / max(float(np.max(np.abs(audio))), 1e-6) * 0.89
    out = CACHE_DIR / f"ref_{_hash_file(path)}.wav"
    sf.write(out, audio, sr)
    consistency = 100.0
    quality = float(np.clip((1 - silence_ratio) * .30 + min(duration / 18, 1) * .20 + min(rms * 22, 1) * .18 + (1 - noise_score) * .17 + (1 - echo) * .15, 0, 1) * 100)
    return ReferenceReport(str(out), path, duration, sr, rms, peak, silence_ratio, noise_score, echo, consistency, quality)


def rank_references(paths: Iterable[str]) -> list[ReferenceReport]:
    """Analyze, estimate cross-reference speaker consistency, and rank references."""
    reports = [report for path in paths for report in _safe_analyze(path)]
    if len(reports) > 1:
        embeddings = []
        for report in reports:
            audio, sr = librosa.load(report.path, sr=24000, mono=True)
            embeddings.append(_embedding(audio, sr))
        centroid = np.mean(np.stack(embeddings), axis=0)
        for report, emb in zip(reports, embeddings):
            denom = float(np.linalg.norm(emb) * np.linalg.norm(centroid) + 1e-8)
            similarity = float(np.dot(emb, centroid) / denom)
            report.speaker_consistency = float(np.clip((similarity + 1) * 50, 0, 100))
            report.quality_score = float(report.quality_score * .82 + report.speaker_consistency * .18)
    return sorted(reports, key=lambda item: item.quality_score, reverse=True)


def _safe_analyze(path: str) -> list[ReferenceReport]:
    """Analyze a path without allowing one bad upload to break the batch."""
    try:
        return [analyze_reference(path)]
    except Exception:
        return []
