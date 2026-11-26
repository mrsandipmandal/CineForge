# CineForge 1-Command Installer (Windows PowerShell)
$ErrorActionPreference = "Stop"

$RepoSpec = if ($env:CINEFORGE_INSTALL_SPEC) { $env:CINEFORGE_INSTALL_SPEC } else { "cineforge" }
$WorkspaceDir = if ($env:CINEFORGE_HOME) { $env:CINEFORGE_HOME } else { Join-Path $HOME ".cineforge" }

Write-Host "==> CineForge Installer" -ForegroundColor Cyan

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "==> Installing uv package manager..."
    irm https://astral.sh/uv/install.ps1 | iex
    $env:Path = "$HOME\.local\bin;$HOME\.cargo\bin;$env:Path"
}

if ((Test-Path "pyproject.toml") -and (Test-Path "pipeline_defs")) {
    Write-Host "==> Detected local CineForge checkout; installing from current directory..."
    uv tool install --force --editable .
} else {
    Write-Host "==> Installing CineForge CLI & MCP server ($RepoSpec)..."
    uv tool install --force $RepoSpec
}

Write-Host "==> Initializing workspace at $WorkspaceDir..."
cineforge init $WorkspaceDir

Write-Host ""
Write-Host "==> Running diagnostic check..."
try { cineforge doctor } catch {}

Write-Host ""
Write-Host "Done! Quick commands:" -ForegroundColor Green
Write-Host "  cineforge setup                        # Guided API key & Remotion/Piper setup"
Write-Host "  cineforge studio                       # Open Backlot Control Room in browser"
Write-Host "  cineforge mcp install --client claude  # Connect Claude Desktop (or cursor/antigravity/vscode)"
Write-Host "  cineforge skills install --target all  # Install portable CineForge AI skills"
