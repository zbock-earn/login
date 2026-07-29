"""Generation history and lightweight job telemetry."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
import json
import time
from settings import OUTPUT_DIR

HISTORY_PATH = OUTPUT_DIR / "history.json"

@dataclass
class GenerationRecord:
    """Metadata for a completed or failed generation."""
    created_at: float
    text_preview: str
    output_path: str
    status: str
    metrics: dict


def _read() -> list[dict]:
    """Read generation history."""
    if not HISTORY_PATH.exists():
        return []
    try:
        return json.loads(HISTORY_PATH.read_text())
    except Exception:
        return []


def append_record(text: str, output_path: str, status: str, metrics: dict) -> None:
    """Append a generation record without raising to the UI."""
    try:
        records = _read()[-99:]
        records.append(asdict(GenerationRecord(time.time(), text[:180], output_path, status, metrics)))
        HISTORY_PATH.write_text(json.dumps(records, indent=2, sort_keys=True))
    except Exception:
        pass


def list_history() -> list[dict]:
    """Return newest generation records first."""
    return list(reversed(_read()))
