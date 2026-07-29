# CosyVoice2 Ultra Voice Generation Studio

A modular, production-oriented Google Colab and Gradio application for local **CosyVoice2-only** text-to-speech. It supports multi-reference voice cloning, long-form chunked synthesis, reference quality analysis, emotion/style prompting, mastering, diagnostics, and WAV/MP3/FLAC/OGG export.

## Features

- CosyVoice2 zero-shot voice generation only; no hosted APIs and no alternate TTS engines.
- Colab bootstrap for system packages, Python dependencies, CosyVoice source installation, CUDA diagnostics, optional Flash Attention detection, and one-time HuggingFace model/tokenizer caching.
- Professional Gradio UI with glassmorphism dark styling, microphone and file references, hardware telemetry, advanced controls, waveform preview, logs, and downloadable exports.
- Long-text pipeline with normalization, sentence/paragraph chunking, custom pronunciations, Roman Urdu hints, automatic emotion detection, and style/prosody instructions.
- Reference analyzer with trimming, normalization, silence/noise/echo detection, quality ranking, and speaker consistency estimates across unlimited uploads.
- Mastering chain with speech EQ, compression, optional noise gate, silence trim, peak normalization, fades, limiter, and soft clipping.

## Run in Colab

Open `CosyVoice2_Ultra_Colab.ipynb` from the repository and click **Run all**. Keep the `CosyVoice2_Ultra/` folder beside the notebook so the modular application files are available.

## Local run

```bash
cd CosyVoice2_Ultra
python -m pip install -r requirements.txt
python app.py
```
