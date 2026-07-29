"""Shared utilities for logging, timing, and runtime diagnostics."""
from __future__ import annotations
import gc, os, platform, random, subprocess, time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator
import numpy as np

@dataclass
class RuntimeInfo:
    """Hardware and Python runtime summary."""
    python: str
    platform: str
    cuda_available: bool
    gpu_name: str
    ram_gb: float
    vram_gb: float

@contextmanager
def timer() -> Iterator[callable]:
    """Yield a callable returning elapsed seconds."""
    start = time.perf_counter()
    yield lambda: time.perf_counter() - start

def set_seed(seed: int) -> None:
    """Seed Python, NumPy, and PyTorch when available."""
    random.seed(seed); np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)
    except Exception:
        pass

def cleanup_memory() -> None:
    """Release Python and CUDA memory after heavy inference."""
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available(): torch.cuda.empty_cache(); torch.cuda.ipc_collect()
    except Exception:
        pass

def runtime_info() -> RuntimeInfo:
    """Return current hardware information without raising."""
    ram = vram = 0.0; gpu = "CPU"; cuda = False
    try:
        import psutil
        ram = psutil.virtual_memory().total / 1024**3
    except Exception: pass
    try:
        import torch
        cuda = torch.cuda.is_available()
        if cuda:
            gpu = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
    except Exception: pass
    return RuntimeInfo(platform.python_version(), platform.platform(), cuda, gpu, ram, vram)

def nvidia_smi() -> str:
    """Return nvidia-smi output for UI diagnostics."""
    try:
        return subprocess.check_output(["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu", "--format=csv,noheader"], text=True).strip()
    except Exception:
        return "GPU telemetry unavailable"
