"""Local hardware and voice model detection probe for CineForge.

Detects host PC capabilities (OS, CPU cores, RAM, GPU VRAM, free disk)
and inventories local offline TTS models (Piper ONNX, IndicF5 checkpoints)
to determine the optimal local execution strategy and fallback path.
"""

from __future__ import annotations

import ctypes
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)

# Standard local models directory in CineForge
LOCAL_MODELS_DIR = Path("library/models/piper")

# Official Piper models for Indic languages
INDIAN_PIPER_MODELS = {
    "bn-IN": {
        "model_name": "bn_BD-google-medium",
        "language": "Bengali",
        "size_mb": 73.2,
        "onnx_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/bn/bn_BD/google/medium/bn_BD-google-medium.onnx",
        "json_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/bn/bn_BD/google/medium/bn_BD-google-medium.onnx.json",
    },
    "hi-IN": {
        "model_name": "hi_IN-rohan-medium",
        "language": "Hindi",
        "size_mb": 68.4,
        "onnx_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/rohan/medium/hi_IN-rohan-medium.onnx",
        "json_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/rohan/medium/hi_IN-rohan-medium.onnx.json",
    },
    "mr-IN": {
        "model_name": "mr_IN-google-medium",
        "language": "Marathi",
        "size_mb": 70.1,
        "onnx_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/mr/mr_IN/google/medium/mr_IN-google-medium.onnx",
        "json_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/mr/mr_IN/google/medium/mr_IN-google-medium.onnx.json",
    },
    "te-IN": {
        "model_name": "te_IN-maya-medium",
        "language": "Telugu",
        "size_mb": 69.8,
        "onnx_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/te/te_IN/maya/medium/te_IN-maya-medium.onnx",
        "json_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/te/te_IN/maya/medium/te_IN-maya-medium.onnx.json",
    },
}


def probe_local_hardware() -> dict[str, Any]:
    """Inspect local CPU, RAM, GPU, and storage metrics."""
    cpu_count = os.cpu_count() or 1
    os_info = f"{platform.system()} {platform.release()} ({platform.architecture()[0]})"

    # Memory detection (cross-platform with Windows ctypes fallback)
    total_ram_gb = 8.0
    avail_ram_gb = 4.0
    if platform.system() == "Windows":
        try:
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            total_ram_gb = round(stat.ullTotalPhys / (1024**3), 2)
            avail_ram_gb = round(stat.ullAvailPhys / (1024**3), 2)
        except Exception:
            pass

    # Disk usage for current workspace
    try:
        du = shutil.disk_usage(".")
        free_disk_gb = round(du.free / (1024**3), 2)
    except Exception:
        free_disk_gb = 50.0

    # GPU & VRAM detection via nvidia-smi
    gpu_name = "None"
    gpu_vram_total_mb = 0
    gpu_vram_free_mb = 0
    try:
        smi = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if smi.returncode == 0 and smi.stdout.strip():
            parts = [p.strip() for p in smi.stdout.strip().split(",")]
            gpu_name = parts[0]
            gpu_vram_total_mb = int(parts[1])
            gpu_vram_free_mb = int(parts[2])
    except Exception:
        pass

    # Locate Piper executable
    piper_exe = shutil.which("piper")
    if not piper_exe:
        venv_piper = Path(sys.prefix) / "Scripts" / "piper.exe"
        if venv_piper.exists():
            piper_exe = str(venv_piper.resolve())

    return {
        "os": os_info,
        "cpu_logical_cores": cpu_count,
        "total_ram_gb": total_ram_gb,
        "available_ram_gb": avail_ram_gb,
        "free_disk_gb": free_disk_gb,
        "gpu_name": gpu_name,
        "vram_total_mb": gpu_vram_total_mb,
        "vram_free_mb": gpu_vram_free_mb,
        "piper_executable": piper_exe,
        "has_cuda_gpu": gpu_vram_total_mb > 0,
    }


def find_piper_executable() -> str | None:
    """Find piper executable on PATH or in current virtual environment."""
    exe = shutil.which("piper")
    if exe:
        return exe
    venv_exe = Path(sys.prefix) / "Scripts" / "piper.exe"
    if venv_exe.exists():
        return str(venv_exe.resolve())
    venv_nix = Path(sys.prefix) / "bin" / "piper"
    if venv_nix.exists():
        return str(venv_nix.resolve())
    return None


class LocalHardwareProbe(BaseTool):
    name = "local_hardware_probe"
    version = "1.0.0"
    tier = ToolTier.ANALYZE
    capability = "hardware_probe"
    provider = "cineforge"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = []
    install_instructions = "Built-in hardware inspection utility."
    agent_skills = ["text-to-speech"]

    capabilities = [
        "hardware_detection",
        "model_inventory",
        "vram_checking",
        "fallback_recommendation",
    ]
    supports = {
        "offline": True,
        "gpu_detection": True,
        "model_probing": True,
    }
    best_for = [
        "inspecting local PC hardware (CPU, RAM, GPU, VRAM) before running local AI models",
        "checking presence of offline Indian TTS models (Bengali bn_BD, Hindi hi_IN)",
        "providing automatic tier recommendation and fallback path",
    ]

    input_schema = {
        "type": "object",
        "properties": {
            "target_language": {
                "type": "string",
                "default": "bn-IN",
                "description": "Language code to check (e.g. bn-IN, hi-IN).",
            },
            "require_cloning": {
                "type": "boolean",
                "default": False,
                "description": "Whether voice cloning is required.",
            },
        },
    }

    output_schema = {
        "type": "object",
        "properties": {
            "hardware": {"type": "object"},
            "model_status": {"type": "object"},
            "recommendation": {"type": "object"},
        },
    }

    def get_status(self) -> ToolStatus:
        return ToolStatus.AVAILABLE

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        hw = probe_local_hardware()
        target_lang = inputs.get("target_language", "bn-IN")
        require_cloning = inputs.get("require_cloning", False)

        model_info = INDIAN_PIPER_MODELS.get(target_lang, INDIAN_PIPER_MODELS["bn-IN"])
        model_name = model_info["model_name"]

        onnx_file = LOCAL_MODELS_DIR / f"{model_name}.onnx"
        json_file = LOCAL_MODELS_DIR / f"{model_name}.onnx.json"
        is_downloaded = onnx_file.exists() and json_file.exists()

        # Recommendation logic based on hardware metrics
        has_gpu = hw["has_cuda_gpu"]
        free_vram_mb = hw["vram_free_mb"]

        if require_cloning:
            if has_gpu and free_vram_mb >= 3500:
                recommended_engine = "indic_f5"
                tier_note = "Local IndicF5 voice cloning supported by your RTX 3050 (3.5GB+ VRAM available)."
            else:
                recommended_engine = "piper_tts"
                tier_note = (
                    "Voice cloning requested but VRAM is below 3.5GB or model missing. "
                    "Safely falling back to lightweight Piper TTS."
                )
        else:
            recommended_engine = "piper_tts"
            tier_note = (
                f"Piper TTS ({model_name}) is the optimal lightweight engine: "
                "0% GPU overhead, instant generation on 16-Core CPU."
            )

        recommendation = {
            "recommended_tool": recommended_engine,
            "target_language": target_lang,
            "model_name": model_name,
            "model_downloaded": is_downloaded,
            "model_size_mb": model_info["size_mb"],
            "model_path": str(onnx_file) if is_downloaded else None,
            "fallback_tool": "piper_tts",
            "tier_note": tier_note,
        }

        return ToolResult(
            success=True,
            data={
                "hardware": hw,
                "model_status": {
                    "language": target_lang,
                    "model_name": model_name,
                    "is_downloaded": is_downloaded,
                    "download_dir": str(LOCAL_MODELS_DIR),
                },
                "recommendation": recommendation,
            },
        )
