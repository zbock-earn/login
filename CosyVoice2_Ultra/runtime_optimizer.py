"""Runtime optimization helpers for Colab GPUs and local CUDA systems."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class OptimizationReport:
    """Summary of runtime acceleration choices."""
    cuda: bool
    gpu_name: str
    mixed_precision: str
    torch_compile_supported: bool
    flash_attention_available: bool
    notes: list[str]


def configure_runtime() -> OptimizationReport:
    """Enable safe PyTorch acceleration flags and report optional features."""
    notes: list[str] = []
    cuda = False
    gpu_name = "CPU"
    mixed_precision = "float32"
    compile_supported = False
    flash = False
    try:
        import torch
        cuda = torch.cuda.is_available()
        compile_supported = hasattr(torch, "compile")
        if cuda:
            gpu_name = torch.cuda.get_device_name(0)
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.benchmark = True
            mixed_precision = "float16/bfloat16 autocast"
            notes.append("Enabled TF32 matmul and cuDNN benchmarking.")
        else:
            notes.append("CUDA unavailable; CPU mode will be slower.")
    except Exception as exc:
        notes.append(f"PyTorch optimization skipped: {exc}")
    try:
        import flash_attn  # noqa: F401
        flash = True
        notes.append("Flash Attention import succeeded.")
    except Exception:
        notes.append("Flash Attention unavailable; using standard attention kernels.")
    return OptimizationReport(cuda, gpu_name, mixed_precision, compile_supported, flash, notes)
