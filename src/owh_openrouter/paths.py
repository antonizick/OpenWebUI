"""XDG-style locations and permission checks."""

from __future__ import annotations

import os
import stat
from pathlib import Path

APP = "owh"


class PermissionProblem(Exception):
    """A secret file or directory has permissions that are too open."""


def config_dir(env: dict[str, str] | None = None) -> Path:
    env = os.environ if env is None else env
    base = env.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / APP


def state_dir(env: dict[str, str] | None = None) -> Path:
    env = os.environ if env is None else env
    base = env.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / APP


def key_file(config: Path | None = None) -> Path:
    return (config or config_dir()) / "openrouter.key"


def ensure_private_dir(path: Path) -> Path:
    """Create `path` (and parents) with mode 0700 on the leaf; tighten it if it exists."""
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)
    return path


def check_private(path: Path) -> None:
    """Raise PermissionProblem if `path` is readable or writable by group or others."""
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise PermissionProblem(f"{path} has mode {mode:04o}; expected no group/world access")
