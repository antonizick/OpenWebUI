"""OpenRouter client (interface only; behaviour arrives in Phase 04)."""

from __future__ import annotations

DEFAULT_URL = "https://openrouter.ai/api/v1"  # expected; confirmed by Phase 03 findings


class OpenRouter:
    def __init__(self, base_url: str, key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._key = key

    def key_info(self) -> dict:
        raise NotImplementedError

    def list_models(self) -> list[dict]:
        raise NotImplementedError
