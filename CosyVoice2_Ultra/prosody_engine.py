"""Prosody controls that translate UI sliders into generation hints."""
from __future__ import annotations

def prosody_prompt(speed: float, voice_strength: float, style_strength: float, creativity: float) -> str:
    """Return human-readable prosody guidance."""
    pace = "slow" if speed < .9 else "fast" if speed > 1.1 else "natural"
    return f"Use a {pace} pace, voice strength {voice_strength:.2f}, style strength {style_strength:.2f}, and creativity {creativity:.2f}."
