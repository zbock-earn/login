"""Emotion and speaking-style prompt engineering."""
from __future__ import annotations
import re

KEYWORDS = {"Happy": ["great", "happy", "wonderful", "congrat"], "Sad": ["sad", "loss", "sorry", "grief"], "Excited": ["amazing", "breaking", "launch", "wow"], "Serious": ["warning", "urgent", "critical"], "Calm": ["relax", "breathe", "peaceful"]}

def detect_emotion(text: str) -> str:
    """Infer a broad emotion from keywords and punctuation."""
    lower = text.lower()
    if lower.count("!") >= 3: return "Very Excited"
    for emotion, words in KEYWORDS.items():
        if any(w in lower for w in words): return emotion
    return "Neutral"

def style_instruction(style: str, emotion: str, preset: str) -> str:
    """Build a concise natural-language prosody instruction for CosyVoice2."""
    return f"Speak in a {style.lower()} style with {emotion.lower()} emotion using the {preset.lower()} preset. Keep pronunciation clear, pauses natural, and voice identity consistent."
