"""Pre-apply snapshots used by `remove` (interface only; behaviour arrives in Phase 04)."""

from __future__ import annotations

from pathlib import Path


def save(state_dir: Path, data: dict) -> Path:
    raise NotImplementedError


def latest(state_dir: Path) -> dict:
    raise NotImplementedError
