"""PC configuration checker — matches local hardware against tool requirements.

Reads .env feature flags (TTS_OFFLINE, LOCAL_VIDEO_MODEL, PREFERRED_TTS_MODEL,
PREFERRED_VIDEO_MODEL) and reports which tools are supported on the current PC.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tools.base_tool import ToolRuntime, ToolStatus
from tools.tool_registry import registry


@dataclass
class PCSpecs:
    """Collected PC hardware and software specifications."""

    cpu_cores: int
    ram_mb: int
    gpu_name: str | None
    vram_mb: int
    disk_free_mb: int
    python_version: str
    node_available: bool
    ffmpeg_available: bool
    cuda_available: bool
    os_name: str
    os_version: str


@dataclass
class ToolMatchResult:
    """Result of matching a single tool against the PC."""

    tool_name: str
    provider: str
    capability: str
    runtime: str
    status: ToolStatus
    supported_models: list[str] = field(default_factory=list)
    blocked_reason: str | None = None
    missing_items: list[str] = field(default_factory=list)
    fix_hint: str | None = None
    is_preferred: bool = False


@dataclass
class PCConfigReport:
    """Full PC configuration report."""

    pc_specs: PCSpecs
    env_flags: dict[str, str | bool]
    results: list[ToolMatchResult] = field(default_factory=list)

    def by_capability(self) -> dict[str, list[ToolMatchResult]]:
        grouped: dict[str, list[ToolMatchResult]] = {}
        for r in self.results:
            grouped.setdefault(r.capability, []).append(r)
        return grouped

    def supported(self) -> list[ToolMatchResult]:
        return [r for r in self.results if r.status == ToolStatus.AVAILABLE]

    def blocked(self) -> list[ToolMatchResult]:
        return [r for r in self.results if r.status != ToolStatus.AVAILABLE]


def _read_env_file() -> dict[str, str]:
    """Read .env file from project root without external dependencies."""
    env_path = Path(".env")
    env_vars: dict[str, str] = {}
    if not env_path.is_file():
        return env_vars
    try:
        text = env_path.read_text(encoding="utf-8")
    except OSError:
        return env_vars
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # Strip inline comments
        if " #" in value:
            value = value[: value.index(" #")].strip()
        if key:
            env_vars[key] = value
    return env_vars


def _detect_gpu() -> tuple[str | None, int, bool]:
    """Detect GPU name, VRAM in MB, and CUDA availability."""
    gpu_name: str | None = None
    vram_mb = 0
    cuda_available = False

    # Try nvidia-smi
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            first_line = result.stdout.strip().splitlines()[0]
            parts = [p.strip() for p in first_line.split(",")]
            if len(parts) >= 2:
                gpu_name = parts[0] or None
                try:
                    vram_mb = int(parts[1])
                except ValueError:
                    vram_mb = 0
                cuda_available = True
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass

    # Try torch CUDA as secondary check
    if not cuda_available:
        try:
            import torch  # type: ignore

            if torch.cuda.is_available():
                cuda_available = True
                if not gpu_name:
                    gpu_name = torch.cuda.get_device_name(0)
                try:
                    vram_mb = int(torch.cuda.get_device_properties(0).total_memory / (1024 * 1024))
                except Exception:
                    vram_mb = 0
        except ImportError:
            pass

    return gpu_name, vram_mb, cuda_available


def _detect_ram() -> int:
    """Detect total RAM in MB."""
    try:
        import psutil  # type: ignore

        return int(psutil.virtual_memory().total / (1024 * 1024))
    except ImportError:
        pass
    # Fallback: read /proc/meminfo on Linux
    try:
        meminfo = Path("/proc/meminfo").read_text(encoding="utf-8")
        for line in meminfo.splitlines():
            if line.startswith("MemTotal:"):
                parts = line.split()
                if len(parts) >= 2:
                    # /proc/meminfo reports kB
                    return int(parts[1]) // 1024
    except OSError:
        pass
    return 0


def _detect_disk_free() -> int:
    """Detect free disk space in MB for current directory."""
    try:
        usage = shutil.disk_usage(".")
        return int(usage.free / (1024 * 1024))
    except OSError:
        return 0


def gather_pc_specs() -> PCSpecs:
    """Collect current PC hardware and software specifications."""
    gpu_name, vram_mb, cuda_available = _detect_gpu()
    return PCSpecs(
        cpu_cores=os.cpu_count() or 1,
        ram_mb=_detect_ram(),
        gpu_name=gpu_name,
        vram_mb=vram_mb,
        disk_free_mb=_detect_disk_free(),
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        node_available=shutil.which("node") is not None,
        ffmpeg_available=shutil.which("ffmpeg") is not None,
        cuda_available=cuda_available,
        os_name=sys.platform,
        os_version=sys.platform,
    )


def _tool_supports_model(tool: Any, model_name: str) -> bool:
    """Check if a tool's input_schema lists the given model in model_id enum."""
    props = tool.input_schema.get("properties", {})
    model_prop = props.get("model_id") or props.get("model") or props.get("model_variant")
    if not model_prop:
        return False
    enum_values = model_prop.get("enum", [])
    return model_name in enum_values


def _extract_supported_models(tool: Any) -> list[str]:
    """Extract supported model names from tool input_schema."""
    props = tool.input_schema.get("properties", {})
    for key in ("model_id", "model", "model_variant"):
        prop = props.get(key)
        if prop and prop.get("enum"):
            return list(prop["enum"])
    return []


def _check_dependencies(tool: Any) -> list[str]:
    """Check tool dependencies and return missing items."""
    missing: list[str] = []
    deps = getattr(tool, "dependencies", []) or []
    for dep in deps:
        if dep.startswith("cmd:"):
            cmd = dep[4:]
            if shutil.which(cmd) is None:
                missing.append(cmd)
        elif dep.startswith("python:"):
            pkg = dep[8:]
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)
        elif dep.startswith("env:"):
            env_var = dep[4:]
            if not os.environ.get(env_var):
                missing.append(env_var)
        else:
            # Unknown dependency format — try as python import
            try:
                __import__(dep)
            except ImportError:
                missing.append(dep)
    return missing


def match_tools_to_pc(pc_specs: PCSpecs, env_flags: dict[str, str | bool]) -> list[ToolMatchResult]:
    """Match all registered tools against PC specs and .env flags."""
    registry.ensure_discovered()
    all_tools = registry.list_all()
    results: list[ToolMatchResult] = []

    # Determine preferred models from env
    preferred_tts = str(env_flags.get("PREFERRED_TTS_MODEL", "") or "").strip()
    preferred_video = str(env_flags.get("PREFERRED_VIDEO_MODEL", "") or "").strip()
    tts_offline = str(env_flags.get("TTS_OFFLINE", "")).lower() == "true"
    local_video = str(env_flags.get("LOCAL_VIDEO_MODEL", "")).lower() == "true"

    for tool_name in all_tools:
        tool = registry.get(tool_name)
        if tool is None:
            continue

        capability = getattr(tool, "capability", "")
        runtime = getattr(tool, "runtime", None)
        provider = getattr(tool, "provider", "")
        info = tool.get_info()

        # Determine if this tool is a preferred model
        is_preferred = False
        if capability == "tts" and preferred_tts and tool_name == preferred_tts.lower().replace(" ", "_"):
            is_preferred = True
        if capability == "video_generation" and preferred_video and tool_name == preferred_video.lower().replace(" ", "_"):
            is_preferred = True

        # --- .env flag gating ---
        # TTS_OFFLINE=true: disable API-backed TTS, keep only LOCAL/LOCAL_GPU
        if capability == "tts" and tts_offline:
            if runtime not in (ToolRuntime.LOCAL, ToolRuntime.LOCAL_GPU):
                results.append(ToolMatchResult(
                    tool_name=tool_name,
                    provider=provider,
                    capability=capability,
                    runtime=runtime.value if runtime else "unknown",
                    status=ToolStatus.UNAVAILABLE,
                    blocked_reason="TTS_OFFLINE=true disables API-backed TTS",
                    missing_items=["TTS_OFFLINE env flag"],
                    fix_hint="Set TTS_OFFLINE=false to enable cloud TTS providers",
                    is_preferred=is_preferred,
                ))
                continue

        # LOCAL_VIDEO_MODEL=true: disable cloud video, keep only LOCAL/LOCAL_GPU
        if capability == "video_generation" and local_video:
            if runtime not in (ToolRuntime.LOCAL, ToolRuntime.LOCAL_GPU):
                results.append(ToolMatchResult(
                    tool_name=tool_name,
                    provider=provider,
                    capability=capability,
                    runtime=runtime.value if runtime else "unknown",
                    status=ToolStatus.UNAVAILABLE,
                    blocked_reason="LOCAL_VIDEO_MODEL=true disables cloud video generation",
                    missing_items=["LOCAL_VIDEO_MODEL env flag"],
                    fix_hint="Set LOCAL_VIDEO_MODEL=false to enable cloud video providers",
                    is_preferred=is_preferred,
                ))
                continue

        # --- Hardware check ---
        resource_profile = getattr(tool, "resource_profile", None)
        hardware_ok = True
        shortfall: list[str] = []
        if resource_profile is not None:
            if pc_specs.cpu_cores < resource_profile.cpu_cores:
                hardware_ok = False
                shortfall.append(f"CPU: need {resource_profile.cpu_cores}, have {pc_specs.cpu_cores}")
            if pc_specs.ram_mb < resource_profile.ram_mb:
                hardware_ok = False
                shortfall.append(f"RAM: need {resource_profile.ram_mb}MB, have {pc_specs.ram_mb}MB")
            if runtime == ToolRuntime.LOCAL_GPU and pc_specs.vram_mb < resource_profile.vram_mb:
                hardware_ok = False
                shortfall.append(f"VRAM: need {resource_profile.vram_mb}MB, have {pc_specs.vram_mb}MB")
            if pc_specs.disk_free_mb < resource_profile.disk_mb:
                hardware_ok = False
                shortfall.append(f"Disk: need {resource_profile.disk_mb}MB, have {pc_specs.disk_free_mb}MB")

        # --- Dependency check ---
        missing_deps = _check_dependencies(tool)

        # --- GPU requirement for LOCAL_GPU tools ---
        if runtime == ToolRuntime.LOCAL_GPU and not pc_specs.cuda_available:
            hardware_ok = False
            shortfall.append("GPU: CUDA-capable GPU not detected")

        # Combine issues
        if not hardware_ok or missing_deps:
            missing_items = shortfall + missing_deps
            fix_hint = getattr(tool, "install_instructions", None)
            if isinstance(fix_hint, str) and fix_hint:
                fix_hint = fix_hint.splitlines()[0] if fix_hint.splitlines() else fix_hint
            results.append(ToolMatchResult(
                tool_name=tool_name,
                provider=provider,
                capability=capability,
                runtime=runtime.value if runtime else "unknown",
                status=ToolStatus.UNAVAILABLE,
                blocked_reason="; ".join(shortfall + missing_deps) or "requirements not met",
                missing_items=missing_items,
                fix_hint=fix_hint,
                supported_models=_extract_supported_models(tool),
                is_preferred=is_preferred,
            ))
            continue

        # Tool is available
        results.append(ToolMatchResult(
            tool_name=tool_name,
            provider=provider,
            capability=capability,
            runtime=runtime.value if runtime else "unknown",
            status=ToolStatus.AVAILABLE,
            supported_models=_extract_supported_models(tool),
            is_preferred=is_preferred,
        ))

    # Sort: available first, then preferred, then by name
    results.sort(key=lambda r: (r.status != ToolStatus.AVAILABLE, not r.is_preferred, r.tool_name))
    return results


def render_report(report: PCConfigReport) -> str:
    """Render a human-readable PC configuration report."""
    lines: list[str] = []
    specs = report.pc_specs
    env = report.env_flags

    lines.append("=" * 60)
    lines.append("CINEFORGE PC CONFIGURATION REPORT")
    lines.append("=" * 60)
    lines.append("")
    lines.append("PC SPECIFICATIONS")
    lines.append("-" * 40)
    lines.append(f"  CPU cores : {specs.cpu_cores}")
    lines.append(f"  RAM       : {specs.ram_mb} MB")
    lines.append(f"  GPU       : {specs.gpu_name or 'None detected'}")
    lines.append(f"  VRAM      : {specs.vram_mb} MB")
    lines.append(f"  Disk free : {specs.disk_free_mb} MB")
    lines.append(f"  Python    : {specs.python_version}")
    lines.append(f"  Node.js   : {'Yes' if specs.node_available else 'No'}")
    lines.append(f"  FFmpeg    : {'Yes' if specs.ffmpeg_available else 'No'}")
    lines.append(f"  CUDA      : {'Yes' if specs.cuda_available else 'No'}")
    lines.append(f"  OS        : {specs.os_name}")
    lines.append("")
    lines.append("ENV FLAGS (.env)")
    lines.append("-" * 40)
    for key, value in env.items():
        lines.append(f"  {key} = {value}")
    lines.append("")

    grouped = report.by_capability()
    for capability in sorted(grouped.keys()):
        results = grouped[capability]
        supported = [r for r in results if r.status == ToolStatus.AVAILABLE]
        blocked = [r for r in results if r.status != ToolStatus.AVAILABLE]

        lines.append(f"CAPABILITY: {capability}  ({len(supported)} supported / {len(blocked)} blocked)")
        lines.append("-" * 60)

        for r in results:
            pref_tag = " [PREFERRED]" if r.is_preferred else ""
            status_tag = "OK" if r.status == ToolStatus.AVAILABLE else "BLOCKED"
            lines.append(f"  [{status_tag}] {r.tool_name}  ({r.provider})  runtime={r.runtime}{pref_tag}")
            if r.supported_models:
                lines.append(f"         models: {', '.join(r.supported_models)}")
            if r.blocked_reason:
                lines.append(f"         reason: {r.blocked_reason}")
            if r.fix_hint:
                lines.append(f"         fix: {r.fix_hint}")
        lines.append("")

    lines.append("=" * 60)
    lines.append(f"TOTAL: {len(report.supported())} supported, {len(report.blocked())} blocked")
    lines.append("=" * 60)
    return "\n".join(lines)


def run_pc_config_check() -> PCConfigReport:
    """Run the full PC configuration check and return a report."""
    pc_specs = gather_pc_specs()
    env_vars = _read_env_file()
    # Merge with actual os.environ (os.environ takes precedence)
    env_flags: dict[str, str | bool] = {}
    for key in ("TTS_OFFLINE", "LOCAL_VIDEO_MODEL", "PREFERRED_TTS_MODEL", "PREFERRED_VIDEO_MODEL"):
        env_flags[key] = os.environ.get(key, env_vars.get(key, ""))

    results = match_tools_to_pc(pc_specs, env_flags)
    report = PCConfigReport(pc_specs=pc_specs, env_flags=env_flags, results=results)
    return report


def main() -> None:
    """CLI entry point: python -m lib.pc_config --report"""
    import argparse

    parser = argparse.ArgumentParser(description="CineForge PC configuration checker")
    parser.add_argument("--report", action="store_true", help="Print PC configuration report")
    args = parser.parse_args()

    if args.report or not any(vars(args).values()):
        report = run_pc_config_check()
        print(render_report(report))


if __name__ == "__main__":
    main()
