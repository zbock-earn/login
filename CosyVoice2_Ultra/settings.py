"""Application settings for CosyVoice2 Ultra Voice Studio."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs"
CACHE_DIR = ROOT / "cache"
MODEL_DIR = ROOT / "models"
ASSET_DIR = ROOT / "assets"
for path in (OUTPUT_DIR, CACHE_DIR, MODEL_DIR, ASSET_DIR):
    path.mkdir(parents=True, exist_ok=True)

@dataclass(frozen=True)
class ModelSettings:
    """CosyVoice2 model and runtime configuration."""
    repo_id: str = "iic/CosyVoice2-0.5B"
    local_dir: Path = MODEL_DIR / "CosyVoice2-0.5B"
    sample_rate: int = 24000
    fp16: bool = True
    jit: bool = False
    trt: bool = False

@dataclass(frozen=True)
class GenerationDefaults:
    """Default generation parameters exposed in the UI."""
    temperature: float = 0.8
    top_p: float = 0.9
    top_k: int = 50
    speed: float = 1.0
    guidance_scale: float = 1.0
    cfg_scale: float = 1.0
    voice_strength: float = 0.85
    style_strength: float = 0.7
    creativity: float = 0.45
    seed: int = 42
    max_chunk_chars: int = 420

MODEL = ModelSettings()
DEFAULTS = GenerationDefaults()
LANGUAGES = ["auto", "en", "zh", "ja", "ko", "es", "fr", "de", "ur", "hi", "ar"]
EMOTIONS = ["Auto", "Neutral", "Happy", "Excited", "Very Excited", "Sad", "Calm", "Serious", "Friendly", "Storytelling", "Podcast", "Documentary", "Motivational", "News", "Tutorial", "Advertisement", "Conversation"]
STYLES = ["Podcast", "Audiobook", "Documentary", "News", "Storytelling", "Teacher", "YouTube", "Shorts", "Conversation", "Narrator", "Commercial", "Motivational"]
PRESETS = ["Studio Narration", "Warm Podcast", "Cinematic Story", "Crisp News", "Energetic Ad", "Calm Tutorial"]
