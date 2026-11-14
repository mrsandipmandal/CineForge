"""VoxCPM2 TTS provider — flow-matching based speech synthesis and voice cloning.

Supports both:
1. Remote Kaggle 2x T4 GPU worker (via trycloudflare tunnel with /clone_voice and /shutdown)
2. Local GPU inference with CUDA
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import requests

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

SESSION_FILE = Path(".kaggle_active_session.json")


def resolve_kaggle_kernel() -> str:
    """Return configured or auto-detected Kaggle kernel slug."""
    explicit = os.environ.get("KAGGLE_KERNEL")
    if explicit:
        return explicit.strip()

    kaggle_bin = shutil.which("kaggle") or "/home/sandip/.local/bin/kaggle"
    if os.path.exists(kaggle_bin):
        try:
            res = subprocess.run(
                [kaggle_bin, "kernels", "list", "--mine", "--csv"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            for line in res.stdout.splitlines():
                parts = line.split(",")
                if len(parts) >= 1:
                    ref = parts[0].strip()
                    if "voxindica" in ref.lower() or "voxcpm2-worker" in ref.lower():
                        return ref
        except Exception:
            pass
    return "mrsandipmandal/voxindica-voxcpm2-worker"


def fetch_live_kaggle_tunnel(kernel_slug: str | None = None) -> tuple[str | None, str | None]:
    """Fetch live trycloudflare.com URL and Bearer token from Kaggle kernel logs."""
    slug = kernel_slug or resolve_kaggle_kernel()
    kaggle_bin = shutil.which("kaggle") or "/home/sandip/.local/bin/kaggle"
    if not os.path.exists(kaggle_bin):
        return None, None

    try:
        proc = subprocess.run(
            [kaggle_bin, "kernels", "logs", slug],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode != 0:
            return None, None

        import re
        match = re.search(r"\[.*\]", proc.stdout, re.DOTALL)
        if match:
            records = json.loads(match.group(0))
            full_text = "".join(r.get("data", "") for r in records)
            urls = re.findall(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", full_text)
            tokens = re.findall(r"BEARER TOKEN\s*:\s*([a-f0-9]{32})", full_text)
            url = urls[-1] if urls else None
            token = tokens[-1] if tokens else None
            return url, token
    except Exception:
        pass
    return None, None


def push_kaggle_kernel(folder_path: str | Path | None = None) -> tuple[bool, str]:
    """Push local notebook folder to Kaggle to start GPU execution."""
    target_dir = Path(folder_path) if folder_path else Path("/media/sandip/Pro/VoxIndica/notebooks/kaggle")
    if not target_dir.is_dir() or not (target_dir / "kernel-metadata.json").is_file():
        return False, f"Invalid kernel folder: {target_dir}"

    kaggle_bin = shutil.which("kaggle") or "/home/sandip/.local/bin/kaggle"
    try:
        proc = subprocess.run(
            [kaggle_bin, "kernels", "push", "-p", str(target_dir)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return proc.returncode == 0, proc.stdout.strip()
    except Exception as e:
        return False, str(e)


class VoxCPM2TTS(BaseTool):
    name = "voxcpm2_tts"
    version = "1.0.0"
    tier = ToolTier.VOICE
    capability = "tts"
    provider = "voxcpm2"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.HYBRID

    install_instructions = (
        "Configure either:\n"
        "  1. Remote Kaggle worker: Run mrsandipmandal/voxindica-voxcpm2-worker on Kaggle\n"
        "     and provide the TUNNEL URL and BEARER TOKEN.\n"
        "  2. Local GPU: pip install voxcpm2 soundfile torch\n"
    )
    fallback = "piper_tts"
    fallback_tools = ["indic_tts", "piper_tts", "mms_tts"]
    agent_skills = ["text-to-speech"]

    capabilities = [
        "text_to_speech",
        "voice_cloning",
        "multilingual",
        "remote_worker",
        "session_shutdown",
    ]
    supports = {
        "voice_cloning": True,
        "multilingual": True,
        "offline": True,
        "remote": True,
        "shutdown": True,
        "native_audio": True,
        "bengali": True,
        "hindi": True,
        "english": True,
    }
    best_for = [
        "High-fidelity zero-shot voice cloning with 3-30s sample",
        "Bengali, Hindi, and Indian English narration",
        "Zero-cost inference on Kaggle 2x T4 GPUs via Cloudflare tunnel",
    ]
    not_good_for = ["Low-bandwidth connections without Kaggle active"]

    input_schema = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Script or text to synthesize.",
            },
            "operation": {
                "type": "string",
                "enum": ["synthesize", "clone_voice", "shutdown", "health"],
                "default": "synthesize",
                "description": "Operation to perform.",
            },
            "tunnel_url": {
                "type": "string",
                "description": "Active trycloudflare.com URL from Kaggle worker.",
            },
            "bearer_token": {
                "type": "string",
                "description": "Bearer token from Kaggle worker.",
            },
            "language": {
                "type": "string",
                "default": "bn-IN",
                "description": "Language code, e.g. bn-IN, hi-IN, en-IN.",
            },
            "reference_audio": {
                "type": "string",
                "description": "Path to reference audio file (or base64 data URI) for voice cloning.",
            },
            "prompt_text": {
                "type": "string",
                "default": "",
                "description": "Transcript of the reference audio clip (optional, improves cloning accuracy).",
            },
            "speed": {
                "type": "number",
                "default": 1.0,
                "description": "Speech speed multiplier.",
            },
            "pitch": {
                "type": "number",
                "default": 1.0,
                "description": "Pitch multiplier.",
            },
            "cfg_value": {
                "type": "number",
                "default": 2.0,
                "description": "Classifier-free guidance strength.",
            },
            "inference_timesteps": {
                "type": "integer",
                "default": 8,
                "description": "Flow-matching inference steps (default 8).",
            },
            "output_path": {
                "type": "string",
                "description": "Target WAV file path.",
            },
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=2, ram_mb=1024, vram_mb=0, disk_mb=200, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["timeout", "connection_error"])
    idempotency_key_fields = ["text", "language", "reference_audio"]
    side_effects = ["writes audio file to output_path", "may call remote Kaggle worker"]
    user_visible_verification = ["Listen to generated audio for voice clone similarity and natural pacing"]

    @classmethod
    def get_active_session(cls) -> dict[str, str]:
        """Read cached runtime session info if present."""
        if SESSION_FILE.is_file():
            try:
                return json.loads(SESSION_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    @classmethod
    def save_active_session(cls, tunnel_url: str, bearer_token: str = "") -> None:
        """Cache runtime tunnel info for seamless execution during the pipeline run."""
        payload = {
            "tunnel_url": tunnel_url.rstrip("/"),
            "bearer_token": bearer_token,
            "updated_at": time.time(),
        }
        SESSION_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def clear_active_session(cls) -> None:
        """Clear cached session file."""
        if SESSION_FILE.exists():
            try:
                SESSION_FILE.unlink()
            except Exception:
                pass

    def _resolve_connection(
        self, inputs: dict[str, Any]
    ) -> tuple[str | None, str | None]:
        """Resolve tunnel URL and token from inputs, cache, or env."""
        tunnel_url = inputs.get("tunnel_url") or os.environ.get("VOXCPM2_SERVER_URL")
        bearer_token = inputs.get("bearer_token") or os.environ.get("VOXCPM2_BEARER_TOKEN")

        if not tunnel_url:
            cached = self.get_active_session()
            tunnel_url = cached.get("tunnel_url")
            if not bearer_token:
                bearer_token = cached.get("bearer_token")

        if not tunnel_url:
            live_url, live_token = fetch_live_kaggle_tunnel()
            if live_url:
                tunnel_url = live_url
                if not bearer_token and live_token:
                    bearer_token = live_token
                self.save_active_session(tunnel_url, bearer_token or "")

        if tunnel_url:
            tunnel_url = tunnel_url.rstrip("/")
            if inputs.get("tunnel_url"):
                self.save_active_session(tunnel_url, bearer_token or "")

        return tunnel_url, bearer_token

    def get_status(self) -> ToolStatus:
        tunnel_url, _ = self._resolve_connection({})
        if tunnel_url:
            return ToolStatus.AVAILABLE
        if os.environ.get("TTS_OFFLINE", "").lower() == "true" and self._cuda_available():
            return ToolStatus.AVAILABLE
        return ToolStatus.AVAILABLE

    def _cuda_available(self) -> bool:
        try:
            import torch  # type: ignore

            return torch.cuda.is_available()
        except ImportError:
            return shutil.which("nvidia-smi") is not None

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def shutdown(self, tunnel_url: str | None = None, token: str | None = None) -> dict[str, Any]:
        """Stop worker via /shutdown endpoint and release Kaggle GPU session via CLI."""
        results: dict[str, Any] = {"http_shutdown": False, "kaggle_cli_stop": False}
        resolved_url, resolved_token = self._resolve_connection({
            "tunnel_url": tunnel_url,
            "bearer_token": token,
        })

        if resolved_url:
            headers = {}
            if resolved_token:
                headers["Authorization"] = f"Bearer {resolved_token}"
            try:
                resp = requests.post(f"{resolved_url}/shutdown", headers=headers, timeout=10)
                results["http_shutdown"] = resp.ok
            except Exception as e:
                results["http_shutdown_error"] = str(e)

        # Trigger Kaggle API stop to release GPU allocation
        kaggle_bin = shutil.which("kaggle") or "/home/sandip/.local/bin/kaggle"
        if os.path.exists(kaggle_bin):
            kernel_slug = resolve_kaggle_kernel()
            try:
                proc = subprocess.run(
                    [kaggle_bin, "kernels", "stop", kernel_slug],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=20,
                )
                results["kaggle_cli_stop"] = proc.returncode == 0
                results["kaggle_output"] = proc.stdout.strip()
            except Exception as e:
                results["kaggle_cli_error"] = str(e)

        self.clear_active_session()
        return results

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        operation = inputs.get("operation", "synthesize")
        tunnel_url, bearer_token = self._resolve_connection(inputs)

        # Handle push command to start remote Kaggle worker
        if operation == "push":
            folder = inputs.get("folder_path")
            success, msg = push_kaggle_kernel(folder)
            return ToolResult(
                success=success,
                data={
                    "operation": "push",
                    "kernel": resolve_kaggle_kernel(),
                    "output": msg,
                    "message": "Kaggle kernel pushed. Check status or fetch tunnel once worker boots.",
                },
                error=None if success else msg,
            )

        # Handle fetch tunnel command
        if operation == "fetch_tunnel":
            url, token = fetch_live_kaggle_tunnel()
            if url:
                self.save_active_session(url, token or "")
                return ToolResult(
                    success=True,
                    data={"operation": "fetch_tunnel", "tunnel_url": url, "bearer_token": token},
                )
            return ToolResult(
                success=False,
                error="Could not find an active trycloudflare.com tunnel in Kaggle logs.",
            )

        # Handle shutdown command
        if operation == "shutdown":
            res = self.shutdown(tunnel_url, bearer_token)
            return ToolResult(
                success=True,
                data={
                    "operation": "shutdown",
                    "details": res,
                    "message": "Kaggle worker and tunnel shutdown signal dispatched successfully.",
                },
            )

        # Handle health check
        if operation == "health":
            if not tunnel_url:
                return ToolResult(success=False, error="No active tunnel URL provided for health probe.")
            try:
                resp = requests.get(f"{tunnel_url}/health", timeout=10)
                return ToolResult(success=resp.ok, data=resp.json())
            except Exception as e:
                return ToolResult(success=False, error=f"Health probe failed: {e}")

        # Voice synthesis / cloning
        text = inputs.get("text", "").strip()
        if not text:
            return ToolResult(success=False, error="'text' is required for speech synthesis.")

        start = time.time()
        output_path = Path(inputs.get("output_path", "projects/output/voxcpm2_narration.wav"))
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if tunnel_url:
            return self._execute_remote(inputs, tunnel_url, bearer_token, output_path, start)
        elif self._cuda_available():
            return self._execute_local(inputs, output_path, start)
        else:
            return ToolResult(
                success=False,
                error=(
                    "No active Kaggle Cloudflare tunnel URL configured and local GPU is not available.\n"
                    "Please provide 'tunnel_url' and 'bearer_token' from your running Kaggle notebook "
                    f"({resolve_kaggle_kernel()})."
                ),
            )

    def _execute_remote(
        self,
        inputs: dict[str, Any],
        tunnel_url: str,
        bearer_token: str | None,
        output_path: Path,
        start_time: float,
    ) -> ToolResult:
        """Call the remote Kaggle FastAPI worker via trycloudflare tunnel."""
        headers = {"Content-Type": "application/json"}
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"

        reference_audio = inputs.get("reference_audio", "")
        # If a local file path is given, encode to base64
        if reference_audio and os.path.isfile(reference_audio):
            try:
                raw_bytes = Path(reference_audio).read_bytes()
                encoded_b64 = base64.b64encode(raw_bytes).decode("ascii")
                reference_audio = f"data:audio/wav;base64,{encoded_b64}"
            except Exception as e:
                return ToolResult(success=False, error=f"Failed to read reference audio: {e}")

        payload = {
            "text": inputs["text"],
            "language": inputs.get("language", "bn-IN"),
            "reference_audio": reference_audio,
            "prompt_text": inputs.get("prompt_text", ""),
            "speed": float(inputs.get("speed", 1.0)),
            "pitch": float(inputs.get("pitch", 1.0)),
            "cfg_value": float(inputs.get("cfg_value", 2.0)),
            "inference_timesteps": int(inputs.get("inference_timesteps", 8)),
        }

        endpoint = f"{tunnel_url}/clone_voice"
        try:
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=300)
            if not resp.ok:
                detail = resp.text[:1000]
                return ToolResult(
                    success=False,
                    error=f"VoxCPM2 remote worker error ({resp.status_code}): {detail}",
                )

            data = resp.json()
            audio_b64 = data.get("audio_base64", "")
            if not audio_b64:
                return ToolResult(success=False, error="Worker returned empty audio data.")

            audio_bytes = base64.b64decode(audio_b64)
            output_path.write_bytes(audio_bytes)

            duration = data.get("duration_seconds")
            sample_rate = data.get("sample_rate", 48000)

            result = ToolResult(
                success=True,
                data={
                    "provider": "voxcpm2",
                    "mode": "remote_kaggle_worker",
                    "output_path": str(output_path),
                    "duration_seconds": duration,
                    "sample_rate": sample_rate,
                    "gpu": data.get("gpu", "Tesla T4"),
                    "vram_used": data.get("vram_used"),
                    "generation_seconds": data.get("generation_seconds"),
                },
                artifacts=[str(output_path)],
                duration_seconds=round(time.time() - start_time, 2),
            )
            return result

        except requests.exceptions.RequestException as exc:
            return ToolResult(
                success=False,
                error=f"Connection error reaching Kaggle tunnel at {tunnel_url}: {exc}",
            )

    def _execute_local(
        self, inputs: dict[str, Any], output_path: Path, start_time: float
    ) -> ToolResult:
        """Local GPU execution fallback if voxcpm is installed locally."""
        try:
            from voxcpm import VoxCPM
            import soundfile as sf

            model = VoxCPM.from_pretrained("openbmb/VoxCPM2", device="cuda")
            kwargs: dict[str, Any] = {
                "cfg_value": float(inputs.get("cfg_value", 2.0)),
                "inference_timesteps": int(inputs.get("inference_timesteps", 8)),
            }
            if inputs.get("reference_audio"):
                kwargs["reference_wav_path"] = inputs["reference_audio"]
            if inputs.get("prompt_text"):
                kwargs["prompt_text"] = inputs["prompt_text"]

            audio = model.generate(text=inputs["text"], **kwargs)
            sr = getattr(model, "sample_rate", 24000)
            sf.write(str(output_path), audio, sr)

            return ToolResult(
                success=True,
                data={"output_path": str(output_path), "mode": "local_gpu"},
                artifacts=[str(output_path)],
                duration_seconds=round(time.time() - start_time, 2),
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Local VoxCPM2 inference failed: {e}")
