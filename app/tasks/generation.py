from pathlib import Path

from app.models.schemas import EmotionPreset
from app.services.audio_library import AudioLibrary
from app.services.postprocess import DeepFilterNetPostProcessor
from app.services.tts_engine import VoiceControls, get_tts_engine
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, name="generate_voice")
def generate_voice(self, payload: dict) -> dict:
    self.update_state(state="PROGRESS", meta={"stage": "preparing", "percent": 5})

    library = AudioLibrary()
    audio_id, output_path = library.new_audio_path(".wav")
    voice_reference = payload.get("voice_reference_path")

    controls = VoiceControls(
        emotion=EmotionPreset(payload.get("emotion", "dramatic")),
        emotional_intensity=float(payload.get("emotional_intensity", 0.7)),
        stability=float(payload.get("stability", 0.55)),
        voice_reference_path=Path(voice_reference) if voice_reference else None,
    )

    self.update_state(state="PROGRESS", meta={"stage": "synthesizing", "percent": 30})
    get_tts_engine().synthesize_to_file(payload["text"], controls, output_path)

    self.update_state(state="PROGRESS", meta={"stage": "polishing", "percent": 85})
    DeepFilterNetPostProcessor().polish(output_path)

    return {"stage": "complete", "percent": 100, "audio_id": audio_id, "path": str(output_path)}
