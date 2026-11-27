"""User-friendly Typer + Rich CLI for CineForge."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

from cineforge_cli import __version__
from cineforge_cli.core import (
    DEMO_DESCRIPTIONS,
    POPULAR_API_KEYS,
    apply_workspace_override,
    build_doctor_report,
    check_api_keys,
    discover_demos,
    install_media_extras,
    install_piper_tts,
    render_demo_video,
    setup_remotion_workspace,
    warm_hyperframes_cache,
    write_env_keys,
)

console = Console()
app = typer.Typer(
    name="cineforge",
    help="CineForge — Autonomous AI Film & Video Production Studio CLI.",
    no_args_is_help=True,
    rich_markup_mode="markdown",
)
tools_app = typer.Typer(help="Discover, inspect, and execute CineForge tools.")
pipelines_app = typer.Typer(help="Inspect CineForge video production pipelines.")
mcp_app = typer.Typer(help="Run or configure the CineForge MCP server.")
skills_app = typer.Typer(help="Install or list portable CineForge agent skills.")

app.add_typer(tools_app, name="tools")
app.add_typer(pipelines_app, name="pipelines")
app.add_typer(mcp_app, name="mcp")
app.add_typer(skills_app, name="skills")


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"cineforge {__version__}")
        raise typer.Exit()


@app.callback()
def root_callback(
    workspace: Optional[Path] = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Override the CineForge workspace directory (sets CINEFORGE_HOME).",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show CineForge version and exit.",
    ),
) -> None:
    """Configure workspace overrides before running any subcommand."""
    apply_workspace_override(workspace)


@app.command()
def init(
    path: Optional[Path] = typer.Argument(
        None,
        help="Target workspace folder (defaults to active workspace or ~/.cineforge).",
    ),
) -> None:
    """Initialize a writable CineForge workspace (projects, .env, config.yaml)."""
    from lib.paths import ensure_workspace_initialized

    target = apply_workspace_override(path) if path else None
    ws = ensure_workspace_initialized(target)
    console.print(
        Panel.fit(
            f"[bold green]Workspace initialized![/bold green]\n\n"
            f"Location: [cyan]{ws}[/cyan]\n"
            f"Projects: [cyan]{ws / 'projects'}[/cyan]\n"
            f"Config:   [cyan]{ws / 'config.yaml'}[/cyan]\n"
            f"Env file: [cyan]{ws / '.env'}[/cyan]\n\n"
            "Next steps:\n"
            "  1. Run [bold]cineforge setup[/bold] for guided setup (optional API keys & runtimes)\n"
            "  2. Run [bold]cineforge doctor[/bold] to check available capabilities\n"
            "  3. Run [bold]cineforge studio[/bold] to open Backlot Control Room\n"
            "  4. Run [bold]cineforge mcp install --client claude[/bold] to connect an AI assistant",
            title="CineForge Init",
        )
    )


@app.command()
def setup(
    non_interactive: bool = typer.Option(
        False,
        "--non-interactive",
        help="Initialize workspace without prompting for API keys or optional installs.",
    ),
    with_remotion: bool = typer.Option(
        False,
        "--with-remotion",
        help="Install Remotion Node.js dependencies into the workspace.",
    ),
    with_piper: bool = typer.Option(
        False,
        "--with-piper",
        help="Install free offline piper-tts via pip.",
    ),
    with_media: bool = typer.Option(
        False,
        "--with-media",
        help="Install zero-key local media extras (yt-dlp, youtube-transcript-api, faster-whisper).",
    ),
    with_hyperframes: bool = typer.Option(
        False,
        "--with-hyperframes",
        help="Pre-warm the npx hyperframes cache.",
    ),
) -> None:
    """Guided interactive setup for workspace, optional API keys, and runtimes."""
    from lib.paths import ensure_workspace_initialized, get_remotion_composer_dir

    ws = ensure_workspace_initialized()
    console.print(f"[bold cyan]CineForge Setup[/bold cyan] — workspace: [green]{ws}[/green]\n")

    report = build_doctor_report()
    bins = report["binaries"]
    console.print(
        f"System check: Python {report['python']['version']} | "
        f"FFmpeg: {'[green]OK[/green]' if bins['ffmpeg']['installed'] else '[yellow]Missing[/yellow]'} | "
        f"Node.js: {'[green]OK[/green]' if bins['node']['installed'] else '[yellow]Missing[/yellow]'}"
    )

    if not bins["ffmpeg"]["installed"]:
        console.print(
            "[yellow]Tip:[/yellow] Install FFmpeg (`sudo apt install ffmpeg`, `brew install ffmpeg`, "
            "or `winget install Gyan.FFmpeg`) for full video assembly."
        )

    if not non_interactive:
        console.print("\n[bold]Optional API Keys[/bold] (press Enter to skip — $0.00 offline mode works right away):")
        collected: dict[str, str] = {}
        for env_name, label, note in POPULAR_API_KEYS:
            already = bool(
                os.environ.get(env_name)
                or (env_name == "GEMINI_API_KEY" and os.environ.get("GOOGLE_API_KEY"))
            )
            prompt_text = f"  {env_name} ({label} — {note})"
            if already:
                console.print(f"  [green]✓[/green] {env_name} already set")
                continue
            val = typer.prompt(prompt_text, default="", show_default=False, hide_input=True)
            if val.strip():
                collected[env_name] = val.strip()

        if collected:
            env_path = write_env_keys(ws / ".env", collected)
            console.print(f"[green]Saved {len(collected)} key(s) to {env_path}[/green]")

        remotion_dir = get_remotion_composer_dir()
        if not with_remotion and bins["node"]["installed"] and not (remotion_dir / "node_modules").is_dir():
            with_remotion = typer.confirm(
                "Install Remotion React composer dependencies into workspace (~700 MB npm install)?",
                default=False,
            )
        if not with_piper:
            try:
                import piper  # type: ignore  # noqa: F401
            except ImportError:
                with_piper = typer.confirm(
                    "Install free offline Piper TTS (`pip install piper-tts`)?",
                    default=False,
                )
        if not with_hyperframes and bins["npx"]["installed"]:
            with_hyperframes = typer.confirm(
                "Pre-warm HyperFrames runtime cache (`npx --yes hyperframes --version`)?",
                default=False,
            )

    if with_remotion:
        ok, msg = setup_remotion_workspace(ws, install_deps=True)
        console.print(f"[{'green' if ok else 'yellow'}]{msg}[/]")

    if with_piper:
        ok, msg = install_piper_tts()
        console.print(f"[{'green' if ok else 'yellow'}]{msg}[/]")

    if with_media:
        ok, msg = install_media_extras()
        console.print(f"[{'green' if ok else 'yellow'}]{msg}[/]")

    if with_hyperframes:
        ok, msg = warm_hyperframes_cache()
        console.print(f"[{'green' if ok else 'yellow'}]{msg}[/]")

    console.print("\n[bold green]Setup complete![/bold green] Run [bold]cineforge doctor[/bold] to verify capabilities.")


@app.command()
def doctor(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON diagnostics."),
    check_keys: bool = typer.Option(False, "--check-keys", help="Probe configured API keys against provider endpoints."),
) -> None:
    """Check installed binaries, render runtimes, and configured AI providers."""
    report = build_doctor_report()
    key_probes = check_api_keys() if check_keys else None
    if key_probes is not None:
        report["key_probes"] = key_probes
    if json_output:
        typer.echo(json.dumps(report, indent=2))
        return

    paths = report["paths"]
    bins = report["binaries"]
    summary = report["provider_summary"]
    runtimes = summary.get("composition_runtimes", {})
    counts = report.get("status_counts") or {}
    env_summary = report.get("env_summary") or []
    env_display = ", ".join(
        f"{item['path']} ({item['nonempty_keys']} keys)" for item in env_summary
    ) or "none found"

    console.print(
        Panel.fit(
            f"[bold]Workspace:[/bold] {paths['workspace_root']}\n"
            f"[bold]Projects:[/bold]  {paths['projects_dir']}\n"
            f"[bold]Package:[/bold]   {paths['package_root']}\n"
            f"[bold]Env files:[/bold] {env_display}\n"
            f"[bold]Tools:[/bold]     {report['total_tools_discovered']} discovered "
            f"([green]{counts.get('available', 0)} ready[/green], "
            f"[yellow]{counts.get('degraded', 0)} degraded[/yellow], "
            f"[dim]{counts.get('unavailable', 0)} unavailable[/dim])",
            title="CineForge Doctor",
        )
    )

    rt_table = Table(title="System & Composition Runtimes")
    rt_table.add_column("Component", style="cyan")
    rt_table.add_column("Status")
    rt_table.add_column("Details")

    rt_table.add_row(
        "FFmpeg",
        "[green]READY[/green]" if runtimes.get("ffmpeg") or bins["ffmpeg"]["installed"] else "[red]MISSING[/red]",
        bins["ffmpeg"].get("version") or bins["ffmpeg"].get("path") or "Install ffmpeg",
    )
    rt_table.add_row(
        "Node.js",
        "[green]READY[/green]" if bins["node"]["installed"] else "[yellow]OPTIONAL[/yellow]",
        bins["node"].get("version") or "Needed for Remotion / HyperFrames",
    )
    rt_table.add_row(
        "Remotion",
        "[green]READY[/green]" if runtimes.get("remotion") else "[yellow]NOT INSTALLED[/yellow]",
        paths["remotion_dir"],
    )
    rt_table.add_row(
        "HyperFrames",
        "[green]READY[/green]" if runtimes.get("hyperframes") else "[yellow]NOT READY[/yellow]",
        "npx hyperframes (Node >= 22 + FFmpeg)",
    )
    console.print(rt_table)

    cap_table = Table(title="Capabilities (Configured / Total)")
    cap_table.add_column("Capability", style="cyan")
    cap_table.add_column("Ready", justify="right")
    cap_table.add_column("Available Providers", style="green")

    for cap in summary.get("capabilities", []):
        avail = ", ".join(cap.get("available_providers", [])) or "-"
        cap_table.add_row(
            cap["capability"],
            f"{cap['configured']}/{cap['total']}",
            avail,
        )
    console.print(cap_table)

    warnings = list(summary.get("runtime_warnings") or []) + list(report.get("env_warnings") or [])
    if warnings:
        console.print("\n[bold yellow]Runtime & Env Warnings:[/bold yellow]")
        for warning in warnings[:8]:
            console.print(f"  - {warning}")

    if key_probes is not None:
        probe_table = Table(title="API Key Live Probes")
        probe_table.add_column("Provider", style="cyan")
        probe_table.add_column("Env Var")
        probe_table.add_column("Status")
        probe_table.add_column("Details")
        for label, info in key_probes.items():
            if not info.get("present"):
                status_str = "[dim]NOT SET[/dim]"
                detail = "-"
            elif info.get("valid") is True:
                status_str = "[green]VALID[/green]"
                detail = f"HTTP {info.get('status_code')}"
            elif info.get("valid") is False:
                status_str = "[red]INVALID[/red]"
                detail = info.get("error") or f"HTTP {info.get('status_code')}"
            else:
                status_str = "[yellow]UNVERIFIED[/yellow]"
                detail = info.get("error") or "network/timeout"
            probe_table.add_row(label, str(info.get("env_var") or "-"), status_str, detail)
        console.print(probe_table)

    popular = report.get("popular_unlocks") or []
    offers = summary.get("setup_offers") or []
    if popular or offers:
        console.print("\n[bold]Quick Unlocks (add env var to workspace .env or run `cineforge setup`):[/bold]")
        shown = 0
        seen_hints: set[str] = set()
        for item in popular:
            console.print(f"  • [cyan]{item['label']}[/cyan]: {item['hint']}")
            seen_hints.add(item["env_var"])
            shown += 1
            if shown >= 8:
                break
        if shown < 8:
            seen_providers: set[str] = set()
            for offer in offers:
                hint = (offer.get("install_instructions") or "").strip()
                prov = str(offer.get("provider") or "")
                env_vars = tuple(offer.get("env_vars") or [])
                dedup_key = prov or (env_vars[0] if env_vars else hint)
                if not hint or hint in seen_hints or dedup_key in seen_providers:
                    continue
                seen_hints.add(hint)
                seen_providers.add(dedup_key)
                short_hint = " ".join(line.strip() for line in hint.splitlines()[:2] if line.strip())
                console.print(f"  • [cyan]{offer['capability']}[/cyan] ({prov}): {short_hint}")
                shown += 1
                if shown >= 8:
                    break

    opt_tools = report.get("optional_package_tools") or []
    if opt_tools:
        console.print(
            "\n[bold]Optional Zero-Key Local Extras[/bold] "
            "(install via [cyan]pip install 'cineforge\\[local]'[/cyan] or individually):"
        )
        for item in opt_tools[:8]:
            console.print(f"  • [cyan]{item['tool']}[/cyan] ({item['capability']}): {item['reason']}")
        if len(opt_tools) > 8:
            console.print(f"  • ... and {len(opt_tools) - 8} more (run `cineforge tools list`)")

    breakdown = report.get("unavailable_breakdown") or {}
    gpu_or_server = breakdown.get("local_gpu", 0) + breakdown.get("external_server", 0)
    if gpu_or_server:
        console.print(
            f"\n[dim]Note: {gpu_or_server} unavailable tool(s) require a local CUDA GPU + model weights "
            "or a running ComfyUI/Blender server. Inspect any tool with `cineforge tools info <name>`.[/dim]"
        )


def _launch_backlot(
    project_id: Optional[str],
    port: Optional[int],
    foreground: bool,
    host: Optional[str] = None,
) -> int:
    from backlot import DEFAULT_PORT
    from backlot.__main__ import cmd_open, cmd_serve

    chosen_port = port or DEFAULT_PORT
    os.environ["BACKLOT_PORT"] = str(chosen_port)
    if host:
        os.environ["BACKLOT_HOST"] = host
    if foreground:
        return cmd_serve(chosen_port, host=host)
    return cmd_open(project_id)


@app.command()
def studio(
    project_id: Optional[str] = typer.Argument(None, help="Optional project ID to open directly."),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Port for the Backlot server (default: 4750)."),
    host: Optional[str] = typer.Option(None, "--host", help="Bind host when running --foreground (default: 127.0.0.1)."),
    foreground: bool = typer.Option(False, "--foreground", "-f", help="Run server in the foreground."),
) -> None:
    """Open the Backlot Matrix Studio control room in your browser."""
    raise typer.Exit(_launch_backlot(project_id, port, foreground, host=host))


@app.command(name="backlot")
def backlot_alias(
    project_id: Optional[str] = typer.Argument(None, help="Optional project ID to open directly."),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Port for the Backlot server."),
    host: Optional[str] = typer.Option(None, "--host", help="Bind host when running --foreground."),
    foreground: bool = typer.Option(False, "--foreground", "-f", help="Run server in the foreground."),
) -> None:
    """Alias for `cineforge studio`."""
    raise typer.Exit(_launch_backlot(project_id, port, foreground, host=host))


@app.command()
def demo(
    name: Optional[str] = typer.Argument(None, help="Specific demo name to render."),
    list_demos: bool = typer.Option(False, "--list", "-l", help="List available zero-key demos."),
) -> None:
    """List or render zero-key Remotion showcase demos."""
    demos = discover_demos()
    if list_demos:
        table = Table(title="Zero-Key Remotion Demos")
        table.add_column("Name", style="cyan")
        table.add_column("Description")
        for demo_key in demos:
            table.add_row(demo_key, DEMO_DESCRIPTIONS.get(demo_key, "Checked-in Remotion demo"))
        console.print(table)
        return

    try:
        outputs = render_demo_video(name)
    except Exception as exc:
        console.print(f"[red]Demo failed:[/red] {exc}")
        raise typer.Exit(1) from exc

    for out in outputs:
        console.print(f"[green]Rendered:[/green] {out}")


@pipelines_app.command("list")
def pipelines_list(
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
) -> None:
    """List all available video production pipelines."""
    from lib.pipeline_loader import list_pipelines, load_pipeline_readonly

    rows = []
    for name in sorted(list_pipelines()):
        try:
            manifest = load_pipeline_readonly(name)
            rows.append(
                {
                    "name": name,
                    "description": manifest.get("description", ""),
                    "stages": [s["name"] for s in manifest.get("stages", [])],
                    "stability": manifest.get("stability", "unknown"),
                }
            )
        except Exception as exc:
            rows.append({"name": name, "description": f"Error: {exc}", "stages": [], "stability": "invalid"})

    if json_output:
        typer.echo(json.dumps(rows, indent=2))
        return

    table = Table(title="CineForge Pipelines")
    table.add_column("Pipeline", style="cyan")
    table.add_column("Stability")
    table.add_column("Stages")
    table.add_column("Description")
    for row in rows:
        table.add_row(row["name"], row["stability"], " → ".join(row["stages"]), row["description"])
    console.print(table)


def _render_pipeline_show(manifest: dict[str, Any]) -> None:
    """Render a structured Rich panel + stages table for a pipeline manifest."""
    orch = manifest.get("orchestration") or {}
    meta_parts = [
        f"[bold]Name:[/bold]        {manifest.get('name', '-')}",
        f"[bold]Version:[/bold]     {manifest.get('version', '-')}",
        f"[bold]Category:[/bold]    {manifest.get('category', '-')}",
        f"[bold]Stability:[/bold]   {manifest.get('stability', '-')}",
        f"[bold]Checkpoint:[/bold]  {manifest.get('default_checkpoint_policy', '-')}",
    ]
    if "budget_default_usd" in orch:
        meta_parts.append(f"[bold]Budget cap:[/bold]  ${orch['budget_default_usd']}")
    desc = " ".join(str(manifest.get("description") or "").split())
    if desc:
        meta_parts.append(f"\n{desc}")

    console.print(Panel.fit("\n".join(meta_parts), title=f"Pipeline: {manifest.get('name', '-')}"))

    stages = manifest.get("stages") or []
    if stages:
        stage_table = Table(title=f"Production Stages ({len(stages)})")
        stage_table.add_column("#", justify="right", style="dim")
        stage_table.add_column("Stage", style="cyan")
        stage_table.add_column("Skill")
        stage_table.add_column("Produces")
        stage_table.add_column("Requires")
        stage_table.add_column("Gate")
        for idx, st in enumerate(stages, 1):
            produces = ", ".join(st.get("produces") or []) or "-"
            requires = ", ".join(st.get("required_artifacts_in") or []) or "-"
            gate = "[yellow]human[/yellow]" if st.get("human_approval_default") else "auto"
            stage_table.add_row(
                str(idx),
                str(st.get("name") or "-"),
                str(st.get("skill") or "-"),
                produces,
                requires,
                gate,
            )
        console.print(stage_table)

    playbooks = manifest.get("compatible_playbooks") or {}
    rec = ", ".join(playbooks.get("recommended") or [])
    also = ", ".join(playbooks.get("also_works") or [])
    if rec or also:
        console.print(
            f"[dim]Playbooks — recommended: {rec or '-'} | also works: {also or '-'}[/dim]"
        )


@pipelines_app.command("show")
def pipelines_show(
    name: str = typer.Argument(..., help="Pipeline name (e.g. animated-explainer)."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
) -> None:
    """Show stage details and tools for a specific pipeline."""
    from lib.pipeline_loader import load_pipeline_readonly

    try:
        manifest = load_pipeline_readonly(name)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    if json_output:
        typer.echo(json.dumps(manifest, indent=2))
        return
    _render_pipeline_show(manifest)


@tools_app.command("list")
def tools_list(
    capability: Optional[str] = typer.Option(None, "--capability", "-c", help="Filter by capability."),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Filter by provider."),
    available_only: bool = typer.Option(False, "--available", "-a", help="Show only ready tools."),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status: available, degraded, or unavailable."),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Substring search on name/best_for."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
) -> None:
    """List CineForge tools discovered by the registry."""
    from tools.tool_registry import registry

    registry.ensure_discovered()
    entries = []
    q_lower = (query or "").strip().lower()
    status_filter = status.strip().lower() if status else None
    for name in sorted(registry.list_all()):
        tool = registry.get(name)
        if tool is None:
            continue
        info = tool.get_info()
        if capability and info.get("capability") != capability:
            continue
        if provider and info.get("provider") != provider:
            continue
        if available_only and info.get("status") != "available":
            continue
        if status_filter and info.get("status") != status_filter:
            continue
        if q_lower:
            haystack = " ".join(
                [name, info.get("capability", ""), info.get("provider", ""), " ".join(info.get("best_for", []))]
            ).lower()
            if q_lower not in haystack:
                continue
        avail = registry.describe_tool_availability(tool)
        entries.append(
            {
                "name": name,
                "capability": info.get("capability"),
                "provider": info.get("provider"),
                "runtime": info.get("runtime"),
                "status": info.get("status"),
                "category": avail["category"],
                "reason": avail["reason"],
            }
        )

    if json_output:
        typer.echo(json.dumps(entries, indent=2))
        return

    table = Table(title=f"CineForge Tools ({len(entries)})")
    table.add_column("Tool", style="cyan")
    table.add_column("Capability")
    table.add_column("Provider")
    table.add_column("Runtime")
    table.add_column("Status")
    table.add_column("Requires / Note")
    has_unavail = False
    for item in entries:
        if item["status"] == "available":
            status_markup = "[green]available[/green]"
            note_markup = "[green]-[/green]"
        elif item["status"] == "degraded":
            has_unavail = True
            status_markup = "[yellow]degraded[/yellow]"
            note_markup = f"[yellow]{item['reason']}[/yellow]"
        else:
            has_unavail = True
            status_markup = "[dim]unavailable[/dim]"
            note_markup = f"[dim]{item['reason']}[/dim]"
        table.add_row(item["name"], item["capability"], item["provider"], item["runtime"], status_markup, note_markup)
    console.print(table)
    if has_unavail:
        console.print(
            "[dim]Tip: Run `cineforge doctor` for prioritized Quick Unlocks, `--available` to filter ready tools, "
            "or `cineforge tools info <name>` for full setup steps.[/dim]"
        )


def _status_badge(status: str) -> str:
    if status == "available":
        return "[green]available[/green]"
    if status == "degraded":
        return "[yellow]degraded[/yellow]"
    return "[dim]unavailable[/dim]"


def _format_constraints(spec: dict[str, Any]) -> str:
    parts: list[str] = []
    if spec.get("enum"):
        parts.append("enum: " + ", ".join(str(v) for v in spec["enum"]))
    if "minimum" in spec or "maximum" in spec:
        lo = spec.get("minimum", "-∞")
        hi = spec.get("maximum", "∞")
        parts.append(f"range: {lo}..{hi}")
    return " | ".join(parts) or "-"


def _render_tool_info(payload: dict[str, Any]) -> None:
    """Render structured Rich panels and tables for `cineforge tools info`."""
    status = str(payload.get("status") or "unknown")
    reason = str(payload.get("availability_reason") or "-")
    category = str(payload.get("availability_category") or "-")
    avail_text = reason if reason == category else f"{reason} ({category})"

    header_lines = [
        f"[bold]Tool:[/bold]         {escape(str(payload.get('name', '-')))} (v{escape(str(payload.get('version', '-')))})",
        f"[bold]Status:[/bold]       {_status_badge(status)} — {escape(avail_text)}",
        f"[bold]Capability:[/bold]   {escape(str(payload.get('capability', '-')))}  |  [bold]Provider:[/bold] {escape(str(payload.get('provider', '-')))}",
        f"[bold]Runtime:[/bold]      {escape(str(payload.get('runtime', '-')))}  |  [bold]Tier:[/bold] {escape(str(payload.get('tier', '-')))}  |  [bold]Stability:[/bold] {escape(str(payload.get('stability', '-')))}",
        f"[bold]Module:[/bold]       {escape(str(payload.get('module_path', '-')))}",
    ]
    console.print(Panel.fit("\n".join(header_lines), title=f"Tool Info: {escape(str(payload.get('name', '-')))}"))

    spec_table = Table(title="Capabilities & Guidance")
    spec_table.add_column("Field", style="cyan", no_wrap=True)
    spec_table.add_column("Details")

    caps = ", ".join(payload.get("capabilities") or []) or "-"
    spec_table.add_row("Capabilities", escape(caps))

    supports = payload.get("supports") or {}
    if supports:
        sup_parts = [f"{k}={v}" for k, v in supports.items()]
        spec_table.add_row("Supports", escape(", ".join(sup_parts)))

    res = payload.get("resource_profile") or {}
    if res:
        spec_table.add_row(
            "Resources",
            f"CPU: {res.get('cpu_cores', '-')} | RAM: {res.get('ram_mb', '-')} MB | "
            f"VRAM: {res.get('vram_mb', '-')} MB | Network: {res.get('network_required', '-')}",
        )

    fallbacks = ", ".join(payload.get("fallback_tools") or []) or str(payload.get("fallback") or "-")
    skills = ", ".join(payload.get("agent_skills") or []) or "-"
    spec_table.add_row("Fallbacks", escape(fallbacks))
    spec_table.add_row("Agent Skills", escape(skills))

    for label, key in (
        ("Best For", "best_for"),
        ("Not Good For", "not_good_for"),
        ("Side Effects", "side_effects"),
    ):
        items = payload.get(key) or []
        if items:
            spec_table.add_row(label, escape("\n".join(f"• {x}" for x in items)))

    console.print(spec_table)

    schema = payload.get("input_schema") or {}
    props = schema.get("properties") or {}
    if props:
        required = set(schema.get("required") or [])
        param_table = Table(title="Input Parameters")
        param_table.add_column("Parameter", style="cyan", no_wrap=True)
        param_table.add_column("Type", no_wrap=True)
        param_table.add_column("Req", no_wrap=True)
        param_table.add_column("Default")
        param_table.add_column("Constraints")
        param_table.add_column("Description")
        for pname, pspec in props.items():
            param_table.add_row(
                escape(str(pname)),
                escape(str(pspec.get("type") or "-")),
                "[bold]yes[/bold]" if pname in required else "no",
                escape(str(pspec.get("default", "-"))),
                escape(_format_constraints(pspec)),
                escape(str(pspec.get("description") or "-")),
            )
        console.print(param_table)

    deps = payload.get("dependencies") or []
    missing = payload.get("missing_dependencies") or []
    inst = (payload.get("install_instructions") or "").strip()
    if deps or missing or inst:
        setup_lines: list[str] = []
        if deps:
            setup_lines.append(f"[bold]Declared deps:[/bold] {escape(', '.join(deps))}")
        if missing:
            setup_lines.append(f"[bold yellow]Missing deps:[/bold yellow]  {escape(', '.join(missing))}")
        if inst:
            setup_lines.append(escape(inst))
        console.print(Panel.fit("\n".join(setup_lines), title="Dependencies & Setup"))


@tools_app.command("info")
def tools_info(
    name: str = typer.Argument(..., help="Registered tool name."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
) -> None:
    """Print contract info, capabilities, and input schema for a tool."""
    from tools.tool_registry import registry

    registry.ensure_discovered()
    tool = registry.get(name)
    if tool is None:
        console.print(f"[red]Unknown tool:[/red] {name}")
        raise typer.Exit(1)
    payload = tool.get_info()
    avail = registry.describe_tool_availability(tool)
    payload["availability_reason"] = avail["reason"]
    payload["availability_category"] = avail["category"]
    payload["missing_dependencies"] = avail["missing_dependencies"]
    if json_output:
        typer.echo(json.dumps(payload, indent=2, default=str))
        return
    _render_tool_info(payload)


@tools_app.command("run")
def tools_run(
    name: str = typer.Argument(..., help="Registered tool name."),
    input_json: str = typer.Option("{}", "--input", "-i", help="JSON object of tool inputs."),
    input_file: Optional[Path] = typer.Option(None, "--input-file", "-f", help="Path to JSON inputs file."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run preflight cost/status check without side effects."),
) -> None:
    """Execute (or dry-run) any registered CineForge tool."""
    from tools.tool_registry import registry

    registry.ensure_discovered()
    tool = registry.get(name)
    if tool is None:
        console.print(f"[red]Unknown tool:[/red] {name}")
        raise typer.Exit(1)

    if input_file:
        payload = json.loads(input_file.read_text(encoding="utf-8"))
    else:
        payload = json.loads(input_json)

    if dry_run:
        typer.echo(json.dumps(tool.dry_run(payload), indent=2, default=str))
        return

    result = tool.execute(payload)
    typer.echo(
        json.dumps(
            {
                "success": result.success,
                "data": result.data,
                "artifacts": result.artifacts,
                "error": result.error,
                "cost_usd": result.cost_usd,
                "duration_seconds": result.duration_seconds,
                "model": result.model,
            },
            indent=2,
            default=str,
        )
    )
    if not result.success:
        raise typer.Exit(1)


@mcp_app.command("run")
def mcp_run(
    transport: str = typer.Option("stdio", "--transport", "-t", help="MCP transport: stdio or streamable-http."),
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host for HTTP transport."),
    port: int = typer.Option(8766, "--port", "-p", help="Port for HTTP transport."),
    all_tools: bool = typer.Option(False, "--all-tools", help="Expose every BaseTool directly as an MCP tool."),
    profile: Optional[str] = typer.Option(
        None, "--profile", help="Comma-separated capability filter (e.g. tts,image_generation)."
    ),
) -> None:
    """Launch the CineForge MCP server."""
    try:
        from cineforge_mcp.server import serve_mcp
    except ImportError as exc:
        console.print(
            "[red]Missing MCP dependency.[/red] Install with: [bold]pip install 'cineforge\\[mcp]'[/bold]"
        )
        raise typer.Exit(1) from exc

    serve_mcp(
        transport=transport,
        host=host,
        port=port,
        all_tools=all_tools,
        profile=profile,
    )


@mcp_app.command("config")
def mcp_config(
    client: str = typer.Option("claude", "--client", "-c", help="Target client (claude, claude-code, cursor, antigravity, windsurf, vscode)."),
    all_tools: bool = typer.Option(False, "--all-tools", help="Include --all-tools in generated command."),
    profile: Optional[str] = typer.Option(None, "--profile", help="Include --profile in generated command."),
    uvx: bool = typer.Option(False, "--uvx", help="Generate zero-install uvx launcher configuration."),
) -> None:
    """Print ready-to-paste MCP client JSON configuration."""
    from cineforge_mcp.installer import build_client_payload, resolve_mcp_launch_spec

    spec = resolve_mcp_launch_spec(all_tools=all_tools, profile=profile, use_uvx=uvx)
    payload = build_client_payload(client, spec)
    typer.echo(json.dumps(payload, indent=2))


@mcp_app.command("install")
def mcp_install(
    client: str = typer.Option(
        "claude",
        "--client",
        "-c",
        help="Target client: claude, claude-code, cursor, antigravity, windsurf, vscode, or all.",
    ),
    all_tools: bool = typer.Option(False, "--all-tools", help="Enable --all-tools mode in MCP config."),
    profile: Optional[str] = typer.Option(None, "--profile", help="Capability profile filter."),
    uvx: bool = typer.Option(False, "--uvx", help="Use uvx launcher instead of local executable."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview config path and payload without writing."),
) -> None:
    """Automatically configure CineForge MCP in Claude Desktop, Cursor, Antigravity, or VS Code."""
    from cineforge_mcp.installer import SUPPORTED_CLIENTS, install_mcp_config

    targets = list(SUPPORTED_CLIENTS) if client == "all" else [client]
    for target in targets:
        try:
            res = install_mcp_config(
                target,
                all_tools=all_tools,
                profile=profile,
                use_uvx=uvx,
                dry_run=dry_run,
            )
        except Exception as exc:
            console.print(f"[red]Failed for {target}:[/red] {exc}")
            if client != "all":
                raise typer.Exit(1) from exc
            continue

        status = "Would update" if dry_run else "Configured"
        console.print(f"[green]{status}[/green] [cyan]{target}[/cyan] → {res['config_path']}")
        if res.get("backup_path"):
            console.print(f"  Backup saved: {res['backup_path']}")


@skills_app.command("list")
def skills_list(
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
) -> None:
    """List bundled CineForge agent skills."""
    from cineforge_cli.skills_installer import list_installable_skills

    items = list_installable_skills()
    if json_output:
        typer.echo(json.dumps(items, indent=2))
        return

    table = Table(title=f"Bundled Agent Skills ({len(items)})")
    table.add_column("Skill", style="cyan")
    table.add_column("Summary")
    for item in items:
        table.add_row(item["name"], item["summary"])
    console.print(table)


@skills_app.command("install")
def skills_install_cmd(
    target: str = typer.Option(
        "agents",
        "--target",
        "-t",
        help="Target IDE/agent: agents, claude, cursor, codex, antigravity, or all.",
    ),
    project_dir: Optional[Path] = typer.Option(
        None,
        "--project-dir",
        "-d",
        help="Target project directory (defaults to current directory).",
    ),
    global_install: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Install into user home directory instead of project directory.",
    ),
    minimal: bool = typer.Option(
        False,
        "--minimal",
        help="Install only the main cineforge skill without extra workflow skills.",
    ),
) -> None:
    """Install portable CineForge skills and slash commands into any project or IDE."""
    from cineforge_cli.skills_installer import install_skills

    try:
        installed = install_skills(
            target,
            project_dir=project_dir,
            global_install=global_install,
            include_workflows=not minimal,
        )
    except Exception as exc:
        console.print(f"[red]Skill install failed:[/red] {exc}")
        raise typer.Exit(1) from exc

    for tgt, paths in installed.items():
        console.print(f"[green]Installed[/green] [cyan]{tgt}[/cyan] ({len(paths)} file(s)):")
        for p in paths:
            console.print(f"  • {p}")


def main(argv: Optional[list[str]] = None) -> None:
    """Console script entry point for `cineforge`."""
    if argv is not None:
        sys.argv = ["cineforge", *argv]
    app()


if __name__ == "__main__":
    main()
