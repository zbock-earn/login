from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EmotionPreset(str, Enum):
    neutral = "neutral"
    deep = "deep"
    whisper = "whisper"
    dramatic = "dramatic"


class GenerationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=12000)
    voice_id: Optional[str] = Field(default=None, description="Reference voice ID for zero-shot cloning")
    emotion: EmotionPreset = EmotionPreset.dramatic
    emotional_intensity: float = Field(default=0.7, ge=0.0, le=1.0)
    stability: float = Field(default=0.55, ge=0.0, le=1.0)
    stream: bool = True


class GenerationResponse(BaseModel):
    job_id: str
    status: str


class AudioAsset(BaseModel):
    id: str
    title: str
    path: str
    duration_seconds: Optional[float] = None
    created_at: str
