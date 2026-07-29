"""CosyVoice2 inference orchestration with chunking, retries, and safe fallbacks."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import time
import numpy as np
from settings import MODEL, OUTPUT_DIR
from cache import ensure_model
from utils import cleanup_memory, set_seed, timer
from preprocessing import build_preprocess_result
from reference_analyzer import rank_references
from audio_mastering import master_audio, write_audio
from diagnostics import audio_metrics
from runtime_optimizer import configure_runtime
from naturalness_engine import NaturalnessProfile, join_with_natural_pauses
from job_manager import append_record

class CosyVoice2Engine:
    """Lazy-loaded CosyVoice2 engine for Gradio and notebooks."""
    def __init__(self) -> None:
        self.model: Any | None = None
        self.sample_rate = MODEL.sample_rate
        self.optimization = configure_runtime()

    def load(self) -> None:
        """Load CosyVoice2 from cached HuggingFace weights exactly once."""
        if self.model is not None:
            return
        model_dir = ensure_model()
        try:
            import torch
            from cosyvoice.cli.cosyvoice import CosyVoice2
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.benchmark = True
            self.model = CosyVoice2(str(model_dir), load_jit=MODEL.jit, load_trt=MODEL.trt, fp16=MODEL.fp16)
            self.sample_rate = int(getattr(self.model, "sample_rate", MODEL.sample_rate))
        except Exception as exc:
            raise RuntimeError(f"Unable to load CosyVoice2 from {model_dir}. Details: {exc}") from exc

    def _infer_chunk(self, text: str, prompt_text: str, prompt_wav: str, params: dict[str, Any]) -> np.ndarray:
        """Generate one chunk using CosyVoice2 zero-shot cloning under inference mode."""
        assert self.model is not None
        import torch
        with torch.inference_mode():
            with torch.autocast("cuda", enabled=torch.cuda.is_available() and MODEL.fp16):
                outputs = self.model.inference_zero_shot(
                    text,
                    prompt_text,
                    prompt_wav,
                    stream=False,
                    speed=float(params.get("speed", 1.0)),
                )
        wavs: list[np.ndarray] = []
        for item in outputs:
            wav = item.get("tts_speech") if isinstance(item, dict) else item
            if isinstance(wav, torch.Tensor):
                wav = wav.detach().cpu().float().numpy()
            wavs.append(np.asarray(wav, dtype=np.float32).flatten())
        return np.concatenate(wavs) if wavs else np.zeros(1, dtype=np.float32)

    def _infer_with_retry(self, chunk: str, prompt_text: str, prompt_wav: str, params: dict[str, Any]) -> np.ndarray:
        """Retry recoverable CUDA/memory errors once after cleanup."""
        try:
            return self._infer_chunk(chunk, prompt_text, prompt_wav, params)
        except RuntimeError as exc:
            if "out of memory" not in str(exc).lower() and "cuda" not in str(exc).lower():
                raise
            cleanup_memory()
            return self._infer_chunk(chunk[: max(80, len(chunk) // 2)], prompt_text, prompt_wav, params)

    def generate(self, text: str, references: list[str], language: str, style: str, emotion: str, preset: str, custom_dict: str, **params: Any) -> tuple[str, dict[str, Any], str]:
        """Normalize, chunk, synthesize, master, save, and return diagnostics."""
        try:
            if not text or not text.strip():
                raise ValueError("Please enter text to synthesize.")
            set_seed(int(params.get("seed", 42)))
            self.load()
            reports = rank_references([path for path in references if path])
            if not reports:
                raise ValueError("Please upload or record at least one usable reference voice.")
            chosen = reports[0]
            prep = build_preprocess_result(
                text=text,
                language=language,
                style=style,
                emotion=emotion,
                preset=preset,
                custom_dictionary=custom_dict,
                max_chunk_chars=int(params.get("max_chunk_chars", 420)),
                speed=float(params.get("speed", 1.0)),
                voice_strength=float(params.get("voice_strength", .85)),
                style_strength=float(params.get("style_strength", .7)),
                creativity=float(params.get("creativity", .45)),
            )
            prompt_text = prep.prompt_instruction[:260]
            pieces: list[np.ndarray] = []
            with timer() as elapsed:
                for index, chunk in enumerate(prep.chunks, start=1):
                    print(f"Generating chunk {index}/{len(prep.chunks)} ({len(chunk)} chars)")
                    pieces.append(self._infer_with_retry(chunk, prompt_text, chosen.path, params))
                profile = NaturalnessProfile(
                    breath_level=float(params.get("breath_level", 0.018)),
                    breath_probability=float(params.get("breath_probability", 0.35)),
                    comma_pause_ms=int(params.get("comma_pause_ms", 120)),
                    sentence_pause_ms=int(params.get("sentence_pause_ms", 260)),
                    paragraph_pause_ms=int(params.get("paragraph_pause_ms", 420)),
                )
                audio = join_with_natural_pauses(pieces, prep.chunks, self.sample_rate, profile, int(params.get("seed", 42)))
                audio = master_audio(audio, self.sample_rate, bool(params.get("normalize", True)), bool(params.get("remove_silence", True)), noise_reduction=bool(params.get("noise_reduction", False)))
                out = OUTPUT_DIR / f"cosyvoice2_ultra_{int(time.time())}.wav"
                write_audio(out, audio, self.sample_rate)
                seconds = elapsed()
            metrics = audio_metrics(audio, self.sample_rate, seconds, prep.detected_emotion)
            metrics.update({
                "Reference Quality": f"{chosen.quality_score:.1f}/100",
                "Speaker Similarity": f"{chosen.speaker_consistency:.1f}/100",
                "Noise Level": f"{chosen.noise_score:.2f}",
                "Echo Level": f"{chosen.echo_score:.2f}",
                "Chunks": len(prep.chunks),
                "GPU Used": self.optimization.gpu_name,
                "VRAM Used": metrics.get("VRAM Used", "see telemetry"),
            })
            append_record(text, str(out), "success", metrics)
            cleanup_memory()
            return str(out), metrics, "Generation completed successfully."
        except Exception as exc:
            append_record(text if "text" in locals() else "", "", "error", {"Error": str(exc)})
            cleanup_memory()
            return "", {"Error": str(exc)}, f"Friendly error: {exc}"

ENGINE = CosyVoice2Engine()
