"""Snapshots of the prior values, written before `apply` changes anything; read by `remove`.

A snapshot holds the whole OpenAI connection config (with keys, so the file is 0600 in a 0700
directory) and the whole task config as Open WebUI returned them, plus where OWH put its
connection (`slot`, `mode`).
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from .paths import check_private, ensure_private_dir

VERSION = 1


def directory(state_dir: Path) -> Path:
    return state_dir / "snapshots"


def save(state_dir: Path, data: dict) -> Path:
    d = ensure_private_dir(directory(state_dir))
    ensure_private_dir(state_dir)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    path = d / f"{stamp}.json"
    payload = {"version": VERSION, "created": stamp, **data}
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    return path


def all_paths(state_dir: Path) -> list[Path]:
    d = directory(state_dir)
    return sorted(d.glob("*.json")) if d.is_dir() else []


def earliest(state_dir: Path) -> Path | None:
    paths = all_paths(state_dir)
    return paths[0] if paths else None


def load(path: Path) -> dict:
    check_private(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != VERSION or "before" not in data:
        raise ValueError(f"{path} is not an OWH snapshot")
    return data
