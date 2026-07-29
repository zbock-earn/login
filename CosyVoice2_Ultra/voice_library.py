"""Persistent local reference voice library for reusable voices."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
import json
import shutil
import time
from settings import CACHE_DIR
from reference_analyzer import ReferenceReport, analyze_reference

LIBRARY_DIR = CACHE_DIR / "voice_library"
LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH = LIBRARY_DIR / "index.json"

@dataclass
class VoiceCard:
    """Metadata for a saved reference voice."""
    voice_id: str
    name: str
    path: str
    created_at: float
    quality_score: float
    duration: float
    noise_score: float
    echo_score: float


def _load_index() -> list[dict]:
    """Load voice library metadata."""
    if not INDEX_PATH.exists():
        return []
    try:
        return json.loads(INDEX_PATH.read_text())
    except Exception:
        return []


def _save_index(items: list[dict]) -> None:
    """Persist voice library metadata atomically."""
    tmp = INDEX_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, indent=2, sort_keys=True))
    tmp.replace(INDEX_PATH)


def save_voice(name: str, source_path: str) -> VoiceCard:
    """Analyze and save a reference voice for future sessions."""
    report = analyze_reference(source_path)
    voice_id = f"voice_{int(time.time())}_{abs(hash(name)) % 10000}"
    dst = LIBRARY_DIR / f"{voice_id}.wav"
    shutil.copyfile(report.path, dst)
    card = VoiceCard(voice_id, name.strip() or voice_id, str(dst), time.time(), report.quality_score, report.duration, report.noise_score, report.echo_score)
    items = [item for item in _load_index() if item.get("voice_id") != voice_id]
    items.append(asdict(card))
    _save_index(items)
    return card


def list_voices() -> list[VoiceCard]:
    """Return saved voices sorted newest first."""
    cards = [VoiceCard(**item) for item in _load_index() if Path(item.get("path", "")).exists()]
    return sorted(cards, key=lambda card: card.created_at, reverse=True)


def resolve_voice_paths(selected_voice_ids: list[str] | None) -> list[str]:
    """Resolve selected voice ids to cached WAV paths."""
    selected = set(selected_voice_ids or [])
    return [card.path for card in list_voices() if card.voice_id in selected]


def choices() -> list[tuple[str, str]]:
    """Return Gradio-compatible choices for saved voices."""
    return [(f"{card.name} · {card.quality_score:.0f}/100", card.voice_id) for card in list_voices()]
