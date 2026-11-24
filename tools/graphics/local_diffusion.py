"""Local Stable Diffusion image generation via diffusers, optimized for low-VRAM."""

from __future__ import annotations

import gc
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import torch
except ImportError:
    torch = None

try:
    from diffusers import StableDiffusionPipeline
except ImportError:
    StableDiffusionPipeline = None

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    RetryPolicy,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)

logger = logging.getLogger(__name__)

class LocalDiffusion(BaseTool):
    name = "local_diffusion"
    version = "1.0.0"
    tier = ToolTier.GENERATE
    capability = "image_generation"
    provider = "local_diffusion"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.SEEDED
    runtime = ToolRuntime.LOCAL_GPU

    install_instructions = (
        "Install diffusers for local Stable Diffusion:\n"
        "  pip install diffusers transformers accelerate torch"
    )

    capabilities = ["generate_image", "generate_illustration", "text_to_image"]
    supports = {
        "negative_prompt": True,
        "seed": True,
        "offline": True,
        "custom_size": True,
        "low_vram_guard": True,
    }
    best_for = [
        "offline/air-gapped generation",
        "low-VRAM environments (RTX 3050 4GB)",
    ]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string"},
            "negative_prompt": {"type": "string", "default": ""},
            "width": {"type": "integer", "default": 512, "description": "Clamped to 512 for low-VRAM"},
            "height": {"type": "integer", "default": 512, "description": "Clamped to 512 for low-VRAM"},
            "model": {
                "type": "string",
                "default": "stabilityai/stable-diffusion-2-1-base",
            },
            "seed": {"type": "integer"},
            "num_inference_steps": {"type": "integer", "default": 25},
            "guidance_scale": {"type": "number", "default": 7.5},
            "output_path": {"type": "string"},
            "low_vram": {"type": "boolean", "default": True},
        },
    }

    def get_status(self) -> ToolStatus:
        try:
            import diffusers  # noqa: F401
            return ToolStatus.AVAILABLE
        except ImportError:
            return ToolStatus.UNAVAILABLE

    def execute(self, inputs: Dict[str, Any]) -> ToolResult:
        if self.get_status() != ToolStatus.AVAILABLE:
            return ToolResult(
                success=False,
                error="diffusers not installed. " + self.install_instructions,
            )

        start = time.time()
        result = generate_local_diffusion_fallback(
            prompt=inputs["prompt"],
            output_path=inputs.get("output_path"),
            negative_prompt=inputs.get("negative_prompt", ""),
            width=inputs.get("width", 512),
            height=inputs.get("height", 512),
            seed=inputs.get("seed"),
            model=inputs.get("model", "stabilityai/stable-diffusion-2-1-base"),
            num_inference_steps=inputs.get("num_inference_steps", 25),
            guidance_scale=inputs.get("guidance_scale", 7.5),
            low_vram=inputs.get("low_vram", True),
        )

        if result["success"]:
            return ToolResult(
                success=True,
                data=result,
                artifacts=[result["output_path"]] if result["output_path"] else [],
                duration_seconds=round(time.time() - start, 2),
            )
        else:
            return ToolResult(success=False, error=result["error"])

def detect_hardware_guard() -> Dict[str, Any]:
    """Detect if hardware is low-VRAM (e.g. RTX 3050 4GB)."""
    if torch is None:
        return {
            "is_cuda": False,
            "is_low_vram": True,
            "total_vram_mb": 0.0,
        }
    try:
        is_cuda = bool(torch.cuda.is_available())
    except Exception:
        is_cuda = False

    gpu_name = ""
    total_vram_mb = 0.0
    if is_cuda:
        try:
            name_val = torch.cuda.get_device_name(0)
            gpu_name = str(name_val) if name_val is not None else ""
        except Exception:
            gpu_name = ""
        try:
            mem_prop = torch.cuda.get_device_properties(0).total_memory
            if isinstance(mem_prop, (int, float)):
                total_vram_mb = float(mem_prop) / (1024 * 1024)
        except Exception:
            total_vram_mb = 0.0

    try:
        is_low_vram = ("3050" in gpu_name.lower()) or (is_cuda and float(total_vram_mb) <= 4600.0)
    except Exception:
        is_low_vram = True

    return {
        "is_cuda": is_cuda,
        "is_low_vram": bool(is_low_vram),
        "total_vram_mb": float(total_vram_mb) if isinstance(total_vram_mb, (int, float)) else 0.0,
    }

def generate_local_diffusion_fallback(
    prompt: str,
    output_path: Optional[str | Path] = None,
    negative_prompt: str = "",
    width: int = 512,
    height: int = 512,
    seed: Optional[int] = None,
    model: str = "stabilityai/stable-diffusion-2-1-base",
    num_inference_steps: int = 25,
    guidance_scale: float = 7.5,
    low_vram: bool = True,
    **kwargs: Any,
) -> Dict[str, Any]:
    
    hardware = detect_hardware_guard()
    # Apply low-VRAM guard if requested or hardware requires it
    should_apply_optimizations = low_vram or hardware["is_low_vram"]
    
    if StableDiffusionPipeline is None:
        return {
            "success": False,
            "error": "diffusers not installed.",
            "provider": "local_diffusion",
        }
        
    if should_apply_optimizations:
        width = min(width, 512)
        height = min(height, 512)
        
    dtype = torch.float16 if hardware["is_cuda"] else torch.float32
    device = "cuda" if hardware["is_cuda"] else "cpu"
    
    try:
        pipe = StableDiffusionPipeline.from_pretrained(
            model,
            torch_dtype=dtype,
        )
        
        if should_apply_optimizations:
            logger.info("Applying low-VRAM optimizations to local diffusion pipeline.")
            if hasattr(pipe, "enable_attention_slicing"):
                pipe.enable_attention_slicing(slice_size="auto")
            if hasattr(pipe, "enable_vae_slicing"):
                pipe.enable_vae_slicing()
            if hasattr(pipe, "enable_model_cpu_offload"):
                pipe.enable_model_cpu_offload()
            else:
                pipe.to(device)
        else:
            pipe.to(device)
            
        generator = torch.Generator(device=device).manual_seed(seed) if seed else None
        
        gc.collect()
        if hardware["is_cuda"]:
            torch.cuda.empty_cache()
            
        image = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            generator=generator,
        ).images[0]
        
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(output_path)
            
        gc.collect()
        if hardware["is_cuda"]:
            torch.cuda.empty_cache()
            
        return {
            "success": True,
            "output_path": str(output_path) if output_path else None,
            "provider": "local_diffusion",
            "model": model,
            "vram_optimized": should_apply_optimizations,
        }
    except Exception as exc:
        logger.error("Local diffusion generation failed: %s", exc)
        return {
            "success": False,
            "error": str(exc),
            "provider": "local_diffusion",
        }
