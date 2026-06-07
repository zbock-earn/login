from pathlib import Path
from typing import Callable

from app.models.schemas import EmotionPreset
from app.services.audio_library import AudioLibrary
from app.services.postprocess import DeepFilterNetPostProcessor
from app.services.tts_engine import VoiceControls, get_tts_engine
from app.tasks.celery_app import celery_app

ProgressCallback = Callable[[str, int], None]


def generate_voice_payload(payload: dict, progress: ProgressCallback | None = None) -> dict:
    """Generate a voice file from a route/Celery payload.

    Keeping the real work outside the Celery task lets the app use the same
    generation pipeline for Celery workers and local no-Redis demo jobs.
    """

    def update(stage: str, percent: int) -> None:
        if progress:
            progress(stage, percent)

    update("preparing", 5)
    library = AudioLibrary()
    audio_id, output_path = library.new_audio_path(".wav")
    voice_reference = payload.get("voice_reference_path")

    controls = VoiceControls(
        emotion=EmotionPreset(payload.get("emotion", "dramatic")),
        emotional_intensity=float(payload.get("emotional_intensity", 0.7)),
        stability=float(payload.get("stability", 0.55)),
        voice_reference_path=Path(voice_reference) if voice_reference else None,
    )

    update("synthesizing", 30)
    get_tts_engine().synthesize_to_file(payload["text"], controls, output_path)

    update("polishing", 85)
    DeepFilterNetPostProcessor().polish(output_path)

    return {"stage": "complete", "percent": 100, "audio_id": audio_id, "path": str(output_path)}


@celery_app.task(bind=True, name="generate_voice")
def generate_voice(self, payload: dict) -> dict:
    return generate_voice_payload(
        payload,
        progress=lambda stage, percent: self.update_state(state="PROGRESS", meta={"stage": stage, "percent": percent}),
    )
