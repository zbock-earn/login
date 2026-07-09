# Fixed F5-TTS Google Colab Code

Copy the complete code cell below into Google Colab and run it.

```python
# Google Colab cell: stable F5-TTS voice cloner with safer stops and less repetition.
# Run this whole file in a Colab code cell.

# 1) Install libraries
!pip install -q f5-tts gradio torch torchaudio scipy librosa soundfile pydub

import os
import re
import tempfile
import traceback
from pathlib import Path

import gradio as gr
import librosa
import numpy as np
import soundfile as sf
import torch
from f5_tts.api import F5TTS

SAMPLE_RATE = 24000
MAX_REF_SECONDS = 14.0
MIN_REF_SECONDS = 3.0
OUTPUT_PATH = "f5_fixed_output.wav"

print("Loading F5-TTS Voice Cloning Engine...")
f5tts = F5TTS()
print("🔥 F5-TTS Model Loaded successfully!")


def normalize_text(text: str, language_mode: str) -> str:
    """Normalize spacing and add a hard sentence ending so F5-TTS stops cleanly."""
    text = (text or "").strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"([.!?।]){2,}", r"\1", text)

    if language_mode == "Hindi / Urdu (Roman)":
        text = text.replace("|", ".")
        if not text.endswith((".", "!", "?")):
            text += "."
    elif language_mode == "Hindi (Devanagari)":
        if not text.endswith(("।", "!", "?")):
            text += "।"
    else:
        if not text.endswith((".", "!", "?")):
            text += "."
    return text


def prepare_reference_audio(ref_audio_path: str) -> tuple[str, str | None]:
    """Load mono audio, remove long silence, and keep a clean 3-14 second prompt."""
    wav, sr = librosa.load(ref_audio_path, sr=SAMPLE_RATE, mono=True)
    if wav.size == 0:
        raise ValueError("Reference audio empty hai. Dobara record/upload karein.")

    wav, _ = librosa.effects.trim(wav, top_db=35)
    duration = len(wav) / SAMPLE_RATE

    warning = None
    if duration < MIN_REF_SECONDS:
        warning = f"⚠️ Reference audio {duration:.1f}s hai; F5-TTS ke liye 3-14s clean audio behtar hoti hai."
    if duration > MAX_REF_SECONDS:
        wav = wav[: int(MAX_REF_SECONDS * SAMPLE_RATE)]
        warning = "⚠️ Reference audio bohat lambi thi; first 14 seconds use kiye gaye."

    peak = float(np.max(np.abs(wav))) if wav.size else 0.0
    if peak > 0:
        wav = 0.95 * wav / peak

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix="_ref.wav")
    sf.write(tmp.name, wav, SAMPLE_RATE)
    return tmp.name, warning


def trim_generated_audio(wav_data, sr: int, max_seconds: float | None = None) -> str:
    """Write generated audio after trimming leading/trailing silence and clipping tails."""
    if hasattr(wav_data, "detach"):
        wav_data = wav_data.detach().cpu().numpy()
    elif hasattr(wav_data, "cpu"):
        wav_data = wav_data.cpu().numpy()

    wav_data = np.asarray(wav_data, dtype=np.float32).squeeze()
    if wav_data.ndim > 1:
        wav_data = librosa.to_mono(wav_data.T if wav_data.shape[0] > wav_data.shape[1] else wav_data)

    wav_data, _ = librosa.effects.trim(wav_data, top_db=40)
    if max_seconds:
        wav_data = wav_data[: int(max_seconds * sr)]

    peak = float(np.max(np.abs(wav_data))) if wav_data.size else 0.0
    if peak > 1.0:
        wav_data = wav_data / peak

    sf.write(OUTPUT_PATH, wav_data, sr)
    return OUTPUT_PATH


def estimate_max_duration_seconds(gen_text: str) -> float:
    """Loose safety cap: prevents endless mumbling/repetition after the requested text."""
    words = max(1, len(gen_text.split()))
    return min(60.0, max(4.0, words / 2.0 + 2.5))


def clone_voice_fixed(gen_text, ref_audio, ref_text, language_mode, speed, seed, remove_silence):
    if not ref_audio:
        return None, "❌ Error: Reference audio zaroori hai."
    if not (gen_text or "").strip():
        return None, "❌ Error: Text to Speak khali hai."
    if not (ref_text or "").strip():
        return None, "❌ Error: Reference Text exact likhna zaroori hai; wrong/missing transcript repetition ka common reason hai."

    ref_path = None
    try:
        gen_text = normalize_text(gen_text, language_mode)
        ref_text = normalize_text(ref_text, language_mode)
        ref_path, ref_warning = prepare_reference_audio(ref_audio)

        infer_kwargs = dict(
            ref_file=ref_path,
            ref_text=ref_text,
            gen_text=gen_text,
            remove_silence=bool(remove_silence),
            speed=float(speed),
            seed=int(seed) if int(seed) >= 0 else -1,
        )

        print("🤖 Generating:", infer_kwargs)
        with torch.inference_mode():
            result = f5tts.infer(**infer_kwargs)

        if isinstance(result, tuple):
            wav_data = result[0]
            sr = int(result[1]) if len(result) > 1 else SAMPLE_RATE
            output_path = trim_generated_audio(wav_data, sr, estimate_max_duration_seconds(gen_text))
        elif isinstance(result, str) and os.path.exists(result):
            wav_data, sr = librosa.load(result, sr=None, mono=True)
            output_path = trim_generated_audio(wav_data, sr, estimate_max_duration_seconds(gen_text))
        else:
            return None, "❌ Error: F5-TTS ne audio return nahi ki."

        msg = "✅ Success! Agar phir repeat ho, Reference Text ko bilkul exact audio transcript banayein aur 6-10 sec clear voice use karein."
        if ref_warning:
            msg = ref_warning + "\n" + msg
        return output_path, msg

    except TypeError as e:
        return None, "❌ F5-TTS API mismatch. Runtime restart karke latest cell dobara run karein. Details: " + str(e)
    except Exception:
        return None, "❌ System Error:\n" + traceback.format_exc()
    finally:
        if ref_path and os.path.exists(ref_path):
            try:
                os.remove(ref_path)
            except OSError:
                pass


with gr.Blocks(theme=gr.themes.Base(primary_hue="blue")) as pro_studio:
    gr.Markdown("<center><h1>🎙️ Fixed F5-TTS Voice Cloner for Colab</h1></center>")
    gr.Markdown(
        "**Important:** Reference audio 6-10 seconds, clean, single speaker, no music/noise. "
        "Reference Text must match the audio exactly; warna model galat words ya repetition kar sakta hai."
    )

    with gr.Row():
        with gr.Column():
            gr.Markdown("### 1. Reference Voice & Exact Transcript")
            audio_input = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Apni clean aawaz record/upload karein")
            ref_text_input = gr.Textbox(label="Exact Reference Text", lines=3, placeholder="Audio mein jo exact bola hai wahi likhein...")
        with gr.Column():
            gr.Markdown("### 2. Text to Generate")
            language_dropdown = gr.Dropdown(
                choices=["English / Auto-Detect", "Hindi / Urdu (Roman)", "Hindi (Devanagari)"],
                value="English / Auto-Detect",
                label="Language Mode",
            )
            gen_text_input = gr.Textbox(label="Text to Speak", lines=4, placeholder="Jo bulwana hai wo yahan likhein...")
            speed_slider = gr.Slider(0.75, 1.25, value=1.0, step=0.05, label="Speed")
            seed_input = gr.Number(value=-1, precision=0, label="Seed (-1 random, fixed number repeatable output ke liye)")
            remove_silence_input = gr.Checkbox(value=True, label="Remove silence during F5-TTS export")
            generate_btn = gr.Button("🚀 Generate Fixed Voice", variant="primary", size="lg")

    status_box = gr.Textbox(label="System Status", interactive=False, lines=4)
    audio_output = gr.Audio(label="🎧 Fixed Cloned Voice")

    generate_btn.click(
        fn=clone_voice_fixed,
        inputs=[gen_text_input, audio_input, ref_text_input, language_dropdown, speed_slider, seed_input, remove_silence_input],
        outputs=[audio_output, status_box],
    )

pro_studio.launch(debug=True, share=True)

```

## Bugs fixed / why the old code repeated words

- The old code guessed `f5tts.infer()` arguments with `inspect.signature`; this can pass the wrong value if the API changes. The fixed code calls the documented arguments directly: `ref_file`, `ref_text`, `gen_text`, `remove_silence`, `speed`, and `seed`.
- Missing or inaccurate reference transcript is a major reason for wrong words and repeated speech. The fixed UI now requires exact `Reference Text` instead of silently using a fake English sentence.
- Long/noisy reference audio can confuse voice cloning. The fixed code trims silence, converts to mono 24 kHz, normalizes volume, and limits the prompt to 14 seconds.
- The old stereo handling used `flatten()`, which can interleave channels and damage audio. The fixed code converts stereo to mono safely.
- The old code only trimmed final output after generation. The fixed code also enables F5-TTS `remove_silence` and applies a duration safety cap based on the requested text length.
- Hindi/Urdu written in Roman letters is different from Hindi Devanagari. The fixed UI includes a separate `Hindi / Urdu (Roman)` mode.
