#!/usr/bin/env bash
set -euo pipefail

# CineForge 1-Command Installer (Linux / macOS / WSL)
# Installs uv (if needed), installs cineforge CLI + MCP server, initializes ~/.cineforge,
# and prints quick-start commands.

REPO_SPEC="${CINEFORGE_INSTALL_SPEC:-cineforge}"
WORKSPACE_DIR="${CINEFORGE_HOME:-$HOME/.cineforge}"

echo "==> CineForge Installer"

if ! command -v uv >/dev/null 2>&1; then
  echo "==> Installing uv package manager..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

if [ -f "pyproject.toml" ] && [ -d "pipeline_defs" ]; then
  echo "==> Detected local CineForge checkout; installing from current directory..."
  uv tool install --force --editable .
else
  echo "==> Installing CineForge CLI & MCP server ($REPO_SPEC)..."
  uv tool install --force "$REPO_SPEC"
fi

export PATH="$HOME/.local/bin:$PATH"

echo "==> Initializing workspace at $WORKSPACE_DIR..."
cineforge init "$WORKSPACE_DIR"

echo ""
echo "==> Running diagnostic check..."
cineforge doctor || true

echo ""
echo "Done! Quick commands:"
echo "  cineforge setup                        # Guided API key & Remotion/Piper setup"
echo "  cineforge studio                       # Open Backlot Control Room in browser"
echo "  cineforge mcp install --client claude  # Connect Claude Desktop (or cursor/antigravity/vscode)"
echo "  cineforge skills install --target all  # Install portable CineForge AI skills"
