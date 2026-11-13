"""Open WebUI admin API client (interface only; behaviour arrives in Phase 04)."""

from __future__ import annotations

DEFAULT_URL = "http://127.0.0.1:8080"


class WebUI:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._token: str | None = None

    def signin(self, email: str, password: str) -> None:
        raise NotImplementedError

    def get_connection_config(self) -> dict:
        raise NotImplementedError

    def update_connection_config(self, config: dict) -> dict:
        raise NotImplementedError

    def get_task_config(self) -> dict:
        raise NotImplementedError

    def update_task_config(self, config: dict) -> dict:
        raise NotImplementedError

    def list_models(self) -> list[dict]:
        raise NotImplementedError
