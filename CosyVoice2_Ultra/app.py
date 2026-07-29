"""Application entry point for CosyVoice2 Ultra."""
from __future__ import annotations
from ui import build_ui

def main() -> None:
    """Launch the Gradio app with Colab-friendly sharing enabled."""
    demo = build_ui()
    demo.queue(default_concurrency_limit=1, max_size=20).launch(share=True, debug=False, show_error=True)

if __name__ == "__main__":
    main()
