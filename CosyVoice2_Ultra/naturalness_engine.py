"""Naturalness utilities for human-like pauses, breaths, and chunk transitions."""
from __future__ import annotations
from dataclasses import dataclass
import math
import re
import numpy as np

@dataclass(frozen=True)
class NaturalnessProfile:
    """Controls for subtle human-like nonverbal timing."""
    breath_level: float = 0.018
    breath_probability: float = 0.35
    comma_pause_ms: int = 120
    sentence_pause_ms: int = 260
    paragraph_pause_ms: int = 420
    transition_crossfade_ms: int = 12


def punctuation_pause_ms(text: str, profile: NaturalnessProfile) -> int:
    """Choose pause duration from the punctuation ending a chunk."""
    stripped = text.strip()
    if not stripped:
        return profile.sentence_pause_ms
    if stripped.endswith(("...", "…")):
        return profile.paragraph_pause_ms
    if stripped.endswith((".", "!", "?", "。", "！", "？")):
        return profile.sentence_pause_ms
    if stripped.endswith((",", ";", ":")):
        return profile.comma_pause_ms
    return profile.comma_pause_ms


def synthetic_breath(sr: int, duration_ms: int = 180, level: float = 0.018, seed: int = 0) -> np.ndarray:
    """Create a very quiet breath-like noise bed for natural transitions."""
    samples = max(1, int(sr * duration_ms / 1000))
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 1, samples).astype(np.float32)
    envelope = np.sin(np.linspace(0, math.pi, samples, dtype=np.float32)) ** 1.7
    return (noise * envelope * level).astype(np.float32)


def join_with_natural_pauses(chunks: list[np.ndarray], source_text_chunks: list[str], sr: int, profile: NaturalnessProfile, seed: int) -> np.ndarray:
    """Merge generated chunks with punctuation-aware pauses and subtle breaths."""
    if not chunks:
        return np.zeros(1, dtype=np.float32)
    merged: list[np.ndarray] = []
    rng = np.random.default_rng(seed)
    for index, chunk in enumerate(chunks):
        merged.append(np.asarray(chunk, dtype=np.float32).flatten())
        if index == len(chunks) - 1:
            continue
        pause_ms = punctuation_pause_ms(source_text_chunks[index], profile)
        pause = np.zeros(int(sr * pause_ms / 1000), dtype=np.float32)
        if rng.random() < profile.breath_probability:
            breath = synthetic_breath(sr, min(220, max(110, pause_ms - 40)), profile.breath_level, seed + index)
            start = max(0, (len(pause) - len(breath)) // 2)
            pause[start:start + len(breath)] += breath[: max(0, min(len(breath), len(pause) - start))]
        merged.append(pause)
    return np.concatenate(merged)


def naturalness_instruction(style: str, emotion: str) -> str:
    """Return prompt guidance for human narration behaviors supported by CosyVoice2."""
    style_lower = style.lower()
    emotion_lower = emotion.lower()
    return (
        f"Use a natural human {style_lower} delivery with {emotion_lower} color, micro-pauses, "
        "subtle breath timing, stable volume, clear consonants, and non-robotic phrasing."
    )
