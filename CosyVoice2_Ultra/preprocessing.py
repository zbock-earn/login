"""End-to-end text preprocessing pipeline for production TTS generation."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from text_normalizer import normalize_text
from chunking import chunk_text
from emotion_engine import detect_emotion, style_instruction
from pronunciation_engine import roman_urdu_hint
from prosody_engine import prosody_prompt
from naturalness_engine import naturalness_instruction

@dataclass(frozen=True)
class PreprocessResult:
    """Normalized script, generated chunks, and style prompt for inference."""
    normalized_text: str
    chunks: list[str]
    detected_emotion: str
    prompt_instruction: str


def build_preprocess_result(
    text: str,
    language: str,
    style: str,
    emotion: str,
    preset: str,
    custom_dictionary: str,
    max_chunk_chars: int,
    speed: float,
    voice_strength: float,
    style_strength: float,
    creativity: float,
) -> PreprocessResult:
    """Normalize text, infer emotion, build prosody instructions, and chunk safely."""
    normalized = normalize_text(text, custom_dictionary)
    final_emotion = detect_emotion(normalized) if emotion == "Auto" else emotion
    instruction_parts = [
        style_instruction(style, final_emotion, preset),
        prosody_prompt(speed, voice_strength, style_strength, creativity),
        roman_urdu_hint(normalized, language),
        naturalness_instruction(style, final_emotion),
        "Preserve speaker identity across chunks with smooth pauses and natural breath timing.",
    ]
    prompt = " ".join(part for part in instruction_parts if part).strip()
    chunks = chunk_text(normalized, max_chars=max_chunk_chars)
    return PreprocessResult(normalized, chunks, final_emotion, prompt)
