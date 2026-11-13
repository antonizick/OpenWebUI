"""The dedicated OpenRouter key: redaction and the 0600 key file."""

from __future__ import annotations

import os
from pathlib import Path

from .paths import PermissionProblem, check_private, ensure_private_dir


def redact(secret: str) -> str:
    """Show at most the first 9 characters and the length, never the rest."""
    return f"{secret[:9]}… ({len(secret)} chars)"


def read_key(path: Path) -> str:
    """Read the key file, refusing one that group or others can access."""
    check_private(path)
    key = path.read_text(encoding="utf-8").strip()
    if not key:
        raise PermissionProblem(f"{path} is empty")
    return key


def write_key(path: Path, key: str) -> None:
    """Write the key with mode 0600 in a 0700 directory, never world-readable on disk."""
    ensure_private_dir(path.parent)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(key.strip() + "\n")
    path.chmod(0o600)
