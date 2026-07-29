"""Text normalization for stable long-form TTS."""
from __future__ import annotations
import re
try:
    from num2words import num2words
except Exception:
    def num2words(value: int) -> str:
        return str(value)

ABBREVIATIONS = {"Dr.": "Doctor", "Mr.": "Mister", "Mrs.": "Misses", "Ms.": "Miss", "Prof.": "Professor", "St.": "Saint", "vs.": "versus", "etc.": "etcetera"}

def normalize_text(text: str, custom_dictionary: str = "") -> str:
    """Normalize URLs, email, numbers, currencies, and custom pronunciations."""
    cleaned = (text or "").strip()
    for src, dst in ABBREVIATIONS.items(): cleaned = cleaned.replace(src, dst)
    for line in custom_dictionary.splitlines():
        if "=" in line:
            src, dst = [p.strip() for p in line.split("=", 1)]
            if src: cleaned = re.sub(rf"\b{re.escape(src)}\b", dst, cleaned, flags=re.I)
    cleaned = re.sub(r"([\w.-]+)@([\w.-]+)", lambda m: f"{m.group(1)} at {m.group(2).replace('.', ' dot ')}", cleaned)
    cleaned = re.sub(r"https?://\S+|www\.\S+", lambda m: re.sub(r"[/:.?=&_-]+", " ", m.group(0)), cleaned)
    cleaned = re.sub(r"\$\s?(\d+(?:\.\d+)?)", lambda m: f"{m.group(1)} dollars", cleaned)
    cleaned = re.sub(r"\b\d{1,2}:\d{2}\b", lambda m: m.group(0).replace(":", " "), cleaned)
    def number(m: re.Match[str]) -> str:
        try: return num2words(int(m.group(0)))
        except Exception: return m.group(0)
    cleaned = re.sub(r"\b\d+\b", number, cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()
