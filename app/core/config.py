from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings for API and worker processes."""

    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", env_file_encoding="utf-8")

    app_name: str = "Cinematic Voice SaaS"
    app_env: str = "development"
    redis_url: str = "redis://localhost:6379/0"
    model_root: Path = Path("/models/styletts2")
    deepfilternet_model_root: Path = Path("/models/deepfilternet")
    storage_root: Path = Path("storage")
    cpu_threads: int = Field(default=4, ge=1, le=64)
    max_upload_mb: int = Field(default=50, ge=1, le=500)
    celery_task_always_eager: bool = False
    background_backend: str = "local"

    @property
    def generated_dir(self) -> Path:
        return self.storage_root / "generated"

    @property
    def voices_dir(self) -> Path:
        return self.storage_root / "voices"


def _resolve_from_project_root(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_root = _resolve_from_project_root(settings.storage_root)
    settings.model_root = _resolve_from_project_root(settings.model_root)
    settings.deepfilternet_model_root = _resolve_from_project_root(settings.deepfilternet_model_root)
    settings.generated_dir.mkdir(parents=True, exist_ok=True)
    settings.voices_dir.mkdir(parents=True, exist_ok=True)
    return settings
