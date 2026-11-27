"""Environment variable loader for CineForge.

Loads .env files from cwd, active workspace, and package root without
overwriting already-exported environment variables.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

from lib.paths import get_env_search_paths


def _parse_dotenv_into_environ(env_path: Path) -> None:
    """Parse a .env file into os.environ for keys not already set."""
    if not env_path.is_file():
        return
    with open(env_path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if value[:1] in ("'", '"'):
                quote = value[0]
                end = value.find(quote, 1)
                value = value[1:end] if end != -1 else value[1:]
            else:
                match = re.search(r"(^|\s)#", value)
                if match:
                    value = value[: match.start()]
                value = value.strip()
            # Ignore blank assignments (such as copied .env.example lines) so they
            # do not poison os.environ or block keys in later .env files.
            if key and value and not os.environ.get(key):
                os.environ[key] = value


def load_env(project_root: Optional[Path] = None) -> None:
    """Load .env files from explicit root or workspace/package cascade."""
    if project_root is not None:
        _parse_dotenv_into_environ(Path(project_root) / ".env")
        return
    for env_path in get_env_search_paths():
        _parse_dotenv_into_environ(env_path)


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get an environment variable with optional default."""
    return os.environ.get(key, default)


def require_env(key: str) -> str:
    """Get a required environment variable. Raises if missing."""
    value = os.environ.get(key)
    if value is None:
        raise EnvironmentError(f"Required environment variable {key!r} is not set")
    return value
