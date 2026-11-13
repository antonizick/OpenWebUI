"""Parse config/openrouter-models.txt: one model ID per line, `#` comments."""

from __future__ import annotations

import re
from pathlib import Path

_ID = re.compile(r"^[A-Za-z0-9._~-]+/[A-Za-z0-9._:~+-]+$")


class AllowlistError(ValueError):
    """The allowlist file is malformed."""


def parse(text: str) -> list[str]:
    seen: set[str] = set()
    ids: list[str] = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if not _ID.match(line):
            raise AllowlistError(f"line {n}: invalid model ID {line!r}")
        if line in seen:
            raise AllowlistError(f"line {n}: duplicate model ID {line!r}")
        seen.add(line)
        ids.append(line)
    return ids


def load(path: Path) -> list[str]:
    return parse(path.read_text(encoding="utf-8"))
