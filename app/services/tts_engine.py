import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import soundfile as sf

from app.core.config import get_settings
from app.models.schemas import EmotionPreset


@dataclass(frozen=True)
class VoiceControls:
    emotion: EmotionPreset
    emotional_intensity: float
    stability: float
    voice_reference_path: Path | None = None


class StyleTTS2Engine:
    """CPU-friendly StyleTTS 2 adapter.

    The methods are intentionally isolated so production teams can swap the
    placeholder synthesis code with their checked-out StyleTTS 2 inference API
    without changing FastAPI routes, Celery tasks, or UI code.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self._model_loaded = False

    def warmup(self) -> None:
        if self._model_loaded:
            return
        os.environ.setdefault("OMP_NUM_THREADS", str(self.settings.cpu_threads))
        os.environ.setdefault("MKL_NUM_THREADS", str(self.settings.cpu_threads))
        try:
            import torch

            torch.set_num_threads(self.settings.cpu_threads)
            torch.set_float32_matmul_precision("high")
            # Production hook:
            # self.model = load_styletts2(self.settings.model_root, mmap=True, device="cpu")
        except ImportError:
            pass
        self._model_loaded = True

    def synthesize_to_file(self, text: str, controls: VoiceControls, output_path: Path) -> Path:
        self.warmup()
        chunks = list(self._chunk_text(text))
        audio_segments = [self._synthesize_chunk(chunk, controls) for chunk in chunks]
        stitched = self._crossfade(audio_segments)
        sf.write(output_path, stitched, 24_000)
        return output_path

    def _chunk_text(self, text: str, max_chars: int = 420) -> Iterable[str]:
        sentences = text.replace("\n", " ").split(". ")
        buffer = ""
        for sentence in sentences:
            candidate = f"{buffer}. {sentence}" if buffer else sentence
            if len(candidate) > max_chars and buffer:
                yield buffer.strip()
                buffer = sentence
            else:
                buffer = candidate
        if buffer.strip():
            yield buffer.strip()

    def _synthesize_chunk(self, text: str, controls: VoiceControls) -> np.ndarray:
        # Placeholder implementation for scaffold validation. Replace with:
        # wav = styletts2.infer(text, speaker=embedding, alpha=..., beta=...)
        seconds = max(1.4, min(12.0, len(text) / 38.0))
        sr = 24_000
        t = np.linspace(0, seconds, int(sr * seconds), endpoint=False)
        base_frequency = {
            EmotionPreset.neutral: 155,
            EmotionPreset.deep: 118,
            EmotionPreset.whisper: 190,
            EmotionPreset.dramatic: 145,
        }[controls.emotion]
        vibrato = 1 + (0.01 + controls.emotional_intensity * 0.025) * np.sin(2 * np.pi * 4.8 * t)
        carrier = np.sin(2 * np.pi * base_frequency * vibrato * t)
        breath_noise = np.random.default_rng(42).normal(0, 0.006, len(t))
        envelope = np.minimum(1.0, np.linspace(0, 8, len(t))) * np.minimum(1.0, np.linspace(8, 0, len(t)))
        gain = 0.10 + controls.emotional_intensity * 0.08
        return ((carrier * gain) + breath_noise * (1 - controls.stability)) * envelope

    def _crossfade(self, segments: list[np.ndarray], fade_samples: int = 1_200) -> np.ndarray:
        if not segments:
            return np.zeros(24_000, dtype=np.float32)
        output = segments[0]
        for segment in segments[1:]:
            fade = min(fade_samples, len(output), len(segment))
            if fade > 0:
                ramp_out = np.linspace(1, 0, fade)
                ramp_in = np.linspace(0, 1, fade)
                output = np.concatenate([output[:-fade], output[-fade:] * ramp_out + segment[:fade] * ramp_in, segment[fade:]])
            else:
                output = np.concatenate([output, segment])
        return output.astype(np.float32)


_engine: StyleTTS2Engine | None = None


def get_tts_engine() -> StyleTTS2Engine:
    global _engine
    if _engine is None:
        _engine = StyleTTS2Engine()
    return _engine
