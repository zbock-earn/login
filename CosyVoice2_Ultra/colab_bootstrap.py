"""Colab bootstrap utilities for install, model caching, and diagnostics."""
from __future__ import annotations
import importlib.util, os, subprocess, sys
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, TextColumn

PROJECT = Path(__file__).resolve().parent
COSYVOICE_SRC = Path("/content/CosyVoice") if Path("/content").exists() else PROJECT.parent / "CosyVoice"


def run(command: list[str] | str) -> None:
    """Run a shell command with progress-friendly logging."""
    print("$", " ".join(command) if isinstance(command, list) else command)
    subprocess.check_call(command, shell=isinstance(command, str))


def install_dependencies() -> None:
    """Install system packages, Python requirements, and CosyVoice source exactly once."""
    with Progress(SpinnerColumn(), TextColumn("{task.description}")) as progress:
        progress.add_task("Installing runtime dependencies", total=None)
        if Path("/content").exists():
            run("apt-get update -y && apt-get install -y ffmpeg sox libsox-dev git git-lfs")
        run([sys.executable, "-m", "pip", "install", "-U", "pip", "setuptools", "wheel"])
        run([sys.executable, "-m", "pip", "install", "-r", str(PROJECT / "requirements.txt")])
        if importlib.util.find_spec("cosyvoice") is None:
            if not COSYVOICE_SRC.exists():
                run(["git", "clone", "--depth", "1", "https://github.com/FunAudioLLM/CosyVoice.git", str(COSYVOICE_SRC)])
            run([sys.executable, "-m", "pip", "install", "-e", str(COSYVOICE_SRC)])


def maybe_restart_runtime() -> None:
    """Restart Colab only when the caller explicitly opts in via environment variable."""
    if os.environ.get("COSYVOICE2_FORCE_RESTART") == "1" and Path("/content").exists():
        os.kill(os.getpid(), 9)
