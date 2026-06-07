from pathlib import Path


class DeepFilterNetPostProcessor:
    """DeepFilterNet polishing adapter.

    The subprocess hook keeps the denoiser optional in development while making
    the production integration point explicit. Install DeepFilterNet in the
    worker image and replace the no-op fallback with the CLI/API invocation that
    matches your chosen release.
    """

    def polish(self, wav_path: Path) -> Path:
        # Production hook example:
        # subprocess.run(["deepFilter", str(wav_path), "--output-dir", str(wav_path.parent)], check=True)
        return wav_path
