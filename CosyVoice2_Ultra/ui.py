"""Professional Gradio interface for CosyVoice2 Ultra."""
from __future__ import annotations
import gradio as gr
from settings import LANGUAGES, EMOTIONS, STYLES, PRESETS, DEFAULTS
from inference import ENGINE
from exporters import export_audio
from utils import runtime_info, nvidia_smi
from voice_library import choices as voice_choices, resolve_voice_paths, save_voice
from job_manager import list_history

CSS = """
:root{--glass:rgba(255,255,255,.08);--edge:rgba(255,255,255,.18)}
.gradio-container{background:radial-gradient(circle at top left,#1b2a4a,#080b12 55%,#020409)!important;color:#f4f7fb;font-family:Inter,ui-sans-serif,system-ui}
.panel{background:var(--glass);border:1px solid var(--edge);border-radius:22px;padding:18px;box-shadow:0 18px 55px rgba(0,0,0,.35);backdrop-filter:blur(16px)}
#generate{background:linear-gradient(135deg,#7c3aed,#06b6d4);border:0;border-radius:18px;font-size:20px;font-weight:800;min-height:60px;animation:pulse 2.4s infinite}
@keyframes pulse{0%{filter:brightness(1)}50%{filter:brightness(1.18)}100%{filter:brightness(1)}}
.metric{font-size:13px;color:#b8c7e0}.title{font-size:36px;font-weight:900;letter-spacing:-.04em}.subtitle{color:#a9b7d0}
"""

def hardware_markdown() -> str:
    """Return current hardware status as Markdown."""
    info = runtime_info()
    return f"""### Hardware Monitor\n- **GPU:** {info.gpu_name}\n- **CUDA:** {info.cuda_available}\n- **RAM:** {info.ram_gb:.1f} GB\n- **VRAM:** {info.vram_gb:.1f} GB\n- **Telemetry:** `{nvidia_smi()}`"""

def save_voice_handler(name: str, file_path: str | None) -> tuple[str, gr.Dropdown]:
    """Save an uploaded reference into the local voice library."""
    if not file_path:
        return "Upload one clean reference file first.", gr.Dropdown(choices=voice_choices())
    card = save_voice(name or "Saved Voice", file_path)
    return f"Saved {card.name} with quality {card.quality_score:.1f}/100.", gr.Dropdown(choices=voice_choices())

def generate_handler(files, mic, saved_voices, text, language, style, emotion, preset, custom_dict, temperature, top_p, top_k, speed, guidance_scale, cfg_scale, voice_strength, style_strength, creativity, seed, max_chunk_chars, normalize, remove_silence, noise_reduction, breath_level, breath_probability, comma_pause_ms, sentence_pause_ms, paragraph_pause_ms, export_format, progress=gr.Progress(track_tqdm=True)):
    """Collect Gradio values, call engine, and export requested format."""
    progress(0.02, desc="Preparing references")
    refs = resolve_voice_paths(saved_voices)
    for item in files or []:
        refs.append(item.name if hasattr(item, "name") else str(item))
    if mic:
        refs.append(mic)
    progress(0.12, desc="Loading CosyVoice2 and generating")
    wav, metrics, status = ENGINE.generate(text, refs, language, style, emotion, preset, custom_dict, temperature=temperature, top_p=top_p, top_k=top_k, speed=speed, guidance_scale=guidance_scale, cfg_scale=cfg_scale, voice_strength=voice_strength, style_strength=style_strength, creativity=creativity, seed=seed, max_chunk_chars=max_chunk_chars, normalize=normalize, remove_silence=remove_silence, noise_reduction=noise_reduction, breath_level=breath_level, breath_probability=breath_probability, comma_pause_ms=comma_pause_ms, sentence_pause_ms=sentence_pause_ms, paragraph_pause_ms=paragraph_pause_ms)
    progress(0.92, desc="Exporting")
    exported = export_audio(wav, export_format) if wav else None
    progress(1.0, desc="Done")
    return exported, exported, metrics, status, hardware_markdown(), list_history()

def build_ui() -> gr.Blocks:
    """Build and return the complete Gradio application."""
    with gr.Blocks(theme=gr.themes.Soft(primary_hue="violet", neutral_hue="slate"), css=CSS, title="CosyVoice2 Ultra Studio") as demo:
        gr.HTML('<div class="title">🎙️ CosyVoice2 Ultra Voice Generation Studio</div><div class="subtitle">Offline CosyVoice2 narration, voice library, natural pauses/breathing, mastering, diagnostics, and export.</div>')
        with gr.Tabs():
            with gr.Tab("Generate"):
                with gr.Row():
                    with gr.Column(scale=5, elem_classes="panel"):
                        text = gr.Textbox(label="Script", lines=12, placeholder="Paste long-form narration, podcast, tutorial, ad copy, or dialogue...")
                        with gr.Row():
                            files = gr.File(label="Reference Voice Uploads", file_count="multiple", file_types=["audio"])
                            mic = gr.Audio(label="Microphone Reference", sources=["microphone"], type="filepath")
                        saved_voices = gr.Dropdown(choices=voice_choices(), multiselect=True, label="Saved Voice Library")
                        with gr.Row():
                            language = gr.Dropdown(LANGUAGES, value="auto", label="Language")
                            style = gr.Dropdown(STYLES, value="Narrator", label="Speaking Style")
                            emotion = gr.Dropdown(EMOTIONS, value="Auto", label="Emotion")
                            preset = gr.Dropdown(PRESETS, value="Studio Narration", label="Preset")
                        custom_dict = gr.Textbox(label="Custom Pronunciation Dictionary", lines=3, placeholder="OpenAI=Open A I\nCosyVoice=Cozy Voice")
                        generate = gr.Button("✨ Generate Professional Voice", elem_id="generate")
                    with gr.Column(scale=3, elem_classes="panel"):
                        hardware = gr.Markdown(hardware_markdown())
                        status = gr.Textbox(label="Status Logs", lines=4)
                        metrics = gr.JSON(label="Diagnostics")
                        audio = gr.Audio(label="Waveform Preview", type="filepath")
                        download = gr.File(label="Download Export")
                with gr.Accordion("Advanced Generation, Naturalness & Mastering Controls", open=False):
                    with gr.Row():
                        temperature = gr.Slider(.1, 1.5, DEFAULTS.temperature, step=.05, label="Temperature")
                        top_p = gr.Slider(.1, 1.0, DEFAULTS.top_p, step=.01, label="Top P")
                        top_k = gr.Slider(1, 100, DEFAULTS.top_k, step=1, label="Top K")
                        speed = gr.Slider(.65, 1.45, DEFAULTS.speed, step=.01, label="Speed")
                    with gr.Row():
                        guidance_scale = gr.Slider(.1, 5, DEFAULTS.guidance_scale, step=.1, label="Guidance Scale")
                        cfg_scale = gr.Slider(.1, 5, DEFAULTS.cfg_scale, step=.1, label="CFG Scale")
                        voice_strength = gr.Slider(0, 1, DEFAULTS.voice_strength, step=.01, label="Voice Strength")
                        style_strength = gr.Slider(0, 1, DEFAULTS.style_strength, step=.01, label="Style Strength")
                    with gr.Row():
                        creativity = gr.Slider(0, 1, DEFAULTS.creativity, step=.01, label="Creativity")
                        seed = gr.Number(DEFAULTS.seed, label="Random Seed", precision=0)
                        max_chunk_chars = gr.Slider(160, 900, DEFAULTS.max_chunk_chars, step=10, label="Max Chunk Characters")
                        export_format = gr.Dropdown(["wav", "mp3", "flac", "ogg"], value="wav", label="Export Format")
                    with gr.Row():
                        breath_level = gr.Slider(0, .06, .018, step=.002, label="Natural Breath Level")
                        breath_probability = gr.Slider(0, 1, .35, step=.05, label="Breath Probability")
                        comma_pause_ms = gr.Slider(40, 400, 120, step=10, label="Comma Pause ms")
                        sentence_pause_ms = gr.Slider(100, 800, 260, step=10, label="Sentence Pause ms")
                        paragraph_pause_ms = gr.Slider(200, 1200, 420, step=20, label="Paragraph Pause ms")
                    with gr.Row():
                        normalize = gr.Checkbox(True, label="Peak/LUFS Normalize")
                        remove_silence = gr.Checkbox(True, label="Remove Silence")
                        noise_reduction = gr.Checkbox(False, label="Gentle Noise Reduction")
            with gr.Tab("Voice Library"):
                with gr.Row(elem_classes="panel"):
                    voice_name = gr.Textbox(label="Voice Name", value="Studio Voice")
                    voice_file = gr.Audio(label="Clean Reference To Save", sources=["upload", "microphone"], type="filepath")
                save_status = gr.Textbox(label="Library Status")
                save_button = gr.Button("💾 Save Reference Voice")
            with gr.Tab("History"):
                history = gr.JSON(label="Generation History", value=list_history())
        generate.click(generate_handler, [files, mic, saved_voices, text, language, style, emotion, preset, custom_dict, temperature, top_p, top_k, speed, guidance_scale, cfg_scale, voice_strength, style_strength, creativity, seed, max_chunk_chars, normalize, remove_silence, noise_reduction, breath_level, breath_probability, comma_pause_ms, sentence_pause_ms, paragraph_pause_ms, export_format], [audio, download, metrics, status, hardware, history])
        save_button.click(save_voice_handler, [voice_name, voice_file], [save_status, saved_voices])
    return demo
