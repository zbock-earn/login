"""Pronunciation helpers including Roman Urdu improvements."""
from __future__ import annotations

def roman_urdu_hint(text: str, language: str) -> str:
    """Add guidance for Roman Urdu or Urdu-adjacent Latin text."""
    if language == "ur" or any(w in text.lower() for w in ["hai", "nahi", "aap", "mera"]):
        return "Use natural Pakistani Roman Urdu pronunciation and avoid English letter spelling."
    return ""
