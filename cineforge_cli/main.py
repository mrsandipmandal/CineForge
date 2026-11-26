"""User-friendly Typer + Rich CLI for CineForge."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from cineforge_cli import __version__
from cineforge_cli.core import (
    DEMO_DESCRIPTIONS,
    POPULAR_API_KEYS,
    apply_workspace_override,
    build_doctor_report,
    discover_demos,
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
            already = bool(os.environ.get(env_name))
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

    if with_hyperframes:
        ok, msg = warm_hyperframes_cache()
        console.print(f"[{'green' if ok else 'yellow'}]{msg}[/]")

    console.print("\n[bold green]Setup complete![/bold green] Run [bold]cineforge doctor[/bold] to verify capabilities.")


@app.command()
def doctor(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON diagnostics."),
) -> None:
    """Check installed binaries, render runtimes, and configured AI providers."""
    report = build_doctor_report()
    if json_output:
        typer.echo(json.dumps(report, indent=2))
        return

    paths = report["paths"]
    bins = report["binaries"]
    summary = report["provider_summary"]
    runtimes = summary.get("composition_runtimes", {})

    console.print(
        Panel.fit(
            f"[bold]Workspace:[/bold] {paths['workspace_root']}\n"
            f"[bold]Projects:[/bold]  {paths['projects_dir']}\n"
            f"[bold]Package:[/bold]   {paths['package_root']}\n"
            f"[bold]Tools:[/bold]     {report['total_tools_discovered']} discovered",
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

    warnings = summary.get("runtime_warnings") or []
    if warnings:
        console.print("\n[bold yellow]Runtime Warnings:[/bold yellow]")
        for warning in warnings[:8]:
            console.print(f"  - {warning}")

    offers = summary.get("setup_offers") or []
    if offers:
        console.print("\n[bold]Quick Unlocks (add env var to .env):[/bold]")
        seen_hints: set[str] = set()
        for offer in offers:
            hint = offer.get("install_instructions") or ""
            if not hint or hint in seen_hints:
                continue
            seen_hints.add(hint)
            console.print(f"  • [cyan]{offer['capability']}[/cyan] ({offer.get('provider')}): {hint}")
            if len(seen_hints) >= 6:
                break


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


@pipelines_app.command("show")
def pipelines_show(name: str = typer.Argument(..., help="Pipeline name (e.g. animated-explainer).")) -> None:
    """Show stage details and tools for a specific pipeline."""
    from lib.pipeline_loader import load_pipeline_readonly

    try:
        manifest = load_pipeline_readonly(name)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    typer.echo(json.dumps(manifest, indent=2))


@tools_app.command("list")
def tools_list(
    capability: Optional[str] = typer.Option(None, "--capability", "-c", help="Filter by capability."),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Filter by provider."),
    available_only: bool = typer.Option(False, "--available", "-a", help="Show only ready tools."),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Substring search on name/best_for."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
) -> None:
    """List CineForge tools discovered by the registry."""
    from tools.tool_registry import registry

    registry.ensure_discovered()
    entries = []
    q_lower = (query or "").strip().lower()
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
        if q_lower:
            haystack = " ".join(
                [name, info.get("capability", ""), info.get("provider", ""), " ".join(info.get("best_for", []))]
            ).lower()
            if q_lower not in haystack:
                continue
        entries.append(
            {
                "name": name,
                "capability": info.get("capability"),
                "provider": info.get("provider"),
                "runtime": info.get("runtime"),
                "status": info.get("status"),
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
    for item in entries:
        status_markup = "[green]available[/green]" if item["status"] == "available" else "[dim]unavailable[/dim]"
        table.add_row(item["name"], item["capability"], item["provider"], item["runtime"], status_markup)
    console.print(table)


@tools_app.command("info")
def tools_info(name: str = typer.Argument(..., help="Registered tool name.")) -> None:
    """Print full contract info and input schema for a tool."""
    from tools.tool_registry import registry

    registry.ensure_discovered()
    tool = registry.get(name)
    if tool is None:
        console.print(f"[red]Unknown tool:[/red] {name}")
        raise typer.Exit(1)
    typer.echo(json.dumps(tool.get_info(), indent=2, default=str))


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
            "[red]Missing MCP dependency.[/red] Install with: [bold]pip install 'cineforge[mcp]'[/bold]"
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
