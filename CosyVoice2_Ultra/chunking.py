"""Long text chunking that preserves paragraphs and sentence boundaries."""
from __future__ import annotations
import re
from typing import List

def split_sentences(text: str) -> list[str]:
    """Split text into sentence-like units."""
    return [s.strip() for s in re.split(r"(?<=[.!?。！？])\s+", text) if s.strip()]

def chunk_text(text: str, max_chars: int = 420) -> List[str]:
    """Create stable TTS chunks no longer than max_chars where possible."""
    chunks: list[str] = []
    for paragraph in [p.strip() for p in text.splitlines() if p.strip()] or [text.strip()]:
        current = ""
        for sentence in split_sentences(paragraph):
            if len(sentence) > max_chars:
                words = sentence.split()
                for word in words:
                    if len(current) + len(word) + 1 > max_chars:
                        if current: chunks.append(current.strip())
                        current = word
                    else: current += " " + word
            elif len(current) + len(sentence) + 1 > max_chars:
                if current: chunks.append(current.strip())
                current = sentence
            else: current = (current + " " + sentence).strip()
        if current: chunks.append(current.strip()); current = ""
    return chunks
