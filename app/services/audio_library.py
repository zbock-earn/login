from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.core.config import get_settings
from app.models.schemas import AudioAsset


class AudioLibrary:
    """Disk-backed generated audio catalog.

    Replace this with PostgreSQL plus object storage when multi-user billing,
    retention policies, and team libraries are introduced.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def new_audio_path(self, suffix: str = ".wav") -> tuple[str, Path]:
        audio_id = uuid4().hex
        return audio_id, self.settings.generated_dir / f"{audio_id}{suffix}"

    def list_assets(self) -> list[AudioAsset]:
        assets: list[AudioAsset] = []
        for path in sorted(self.settings.generated_dir.glob("*.wav"), reverse=True):
            stat = path.stat()
            assets.append(
                AudioAsset(
                    id=path.stem,
                    title=f"Generated narration {path.stem[:8]}",
                    path=str(path),
                    created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                )
            )
        return assets

    def resolve_audio(self, audio_id: str) -> Path:
        path = self.settings.generated_dir / f"{audio_id}.wav"
        if not path.exists():
            raise FileNotFoundError(audio_id)
        return path
