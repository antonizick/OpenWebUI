"""The dedicated OpenRouter key: format check, redaction, scrubbing and the 0600 key file."""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

from .paths import PermissionProblem, check_private, ensure_private_dir

KEY_FORMAT = re.compile(r"^sk-or-v1-[0-9a-f]{64}$")
_KEY_LIKE = re.compile(r"sk-or-v1-[0-9A-Za-z]+")
_JWT_LIKE = re.compile(r"eyJ[\w-]+\.[\w-]+\.[\w-]+")

# Values seen this run (key, password, token) that must never reach output.
_registered: set[str] = set()


class KeyFormatError(ValueError):
    """The text is not a well-formed OpenRouter key."""


def redact(secret: str) -> str:
    """Show at most the first 9 characters and the length, never the rest."""
    return f"{secret[:9]}… ({len(secret)} chars)"


def register(*values: str | None) -> None:
    """Remember secrets so `scrub` removes them from any text that is about to be shown."""
    for v in values:
        if v and len(v) >= 4:
            _registered.add(v)


def scrub(text: str) -> str:
    """Remove registered secrets and anything shaped like a key or a JWT."""
    for v in sorted(_registered, key=len, reverse=True):
        text = text.replace(v, "<redacted>")
    text = _KEY_LIKE.sub(lambda m: redact(m.group(0)), text)
    return _JWT_LIKE.sub("<token>", text)


def clean_key(raw: str) -> str:
    """Trim whitespace, reject control characters, check the format. Returns the key."""
    key = raw.strip()
    if any(ord(c) < 0x20 or ord(c) == 0x7F for c in key):
        raise KeyFormatError("the key contains control characters (arrow keys or a paste glitch?)")
    if not KEY_FORMAT.match(key):
        raise KeyFormatError(
            f"not an OpenRouter key: expected sk-or-v1- plus 64 hex characters, "
            f"got {len(key)} characters starting {key[:9]!r}"
        )
    return key


def read_key(path: Path) -> str:
    """Read the key file, refusing one that group or others can access."""
    check_private(path)
    key = path.read_text(encoding="utf-8").strip()
    if not key:
        raise PermissionProblem(f"{path} is empty")
    return key


def write_key(path: Path, key: str) -> None:
    """Write the key atomically: a 0600 temp file in the 0700 directory, then rename."""
    ensure_private_dir(path.parent)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".openrouter.key.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            os.fchmod(fh.fileno(), 0o600)
            fh.write(key.strip() + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
