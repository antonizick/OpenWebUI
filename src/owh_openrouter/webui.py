"""Open WebUI 0.13.3 admin API client (endpoints in docs/OWH_FINDINGS.md §2 and §4)."""

from __future__ import annotations

from . import net
from .secrets import register

DEFAULT_URL = "http://127.0.0.1:8080"
OPENAI_FIELDS = (
    "ENABLE_OPENAI_API",
    "OPENAI_API_BASE_URLS",
    "OPENAI_API_KEYS",
    "OPENAI_API_CONFIGS",
)


class WebUI:
    def __init__(self, base_url: str, timeout: float = 15.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._token: str | None = None

    def _call(self, method: str, path: str, body: object | None = None) -> object:
        return net.request(
            method, self.base_url + path, body=body, token=self._token, timeout=self.timeout
        )

    def version(self) -> str:
        body = self._call("GET", "/api/version")
        return str(body.get("version", "?")) if isinstance(body, dict) else "?"

    def signin(self, email: str, password: str) -> str:
        """Sign in and keep the token in memory. Returns the account's role."""
        register(password)
        body = self._call("POST", "/api/v1/auths/signin", {"email": email, "password": password})
        if not isinstance(body, dict) or not body.get("token"):
            raise net.HttpError(self.base_url, 200, "sign-in answer had no token")
        self._token = body["token"]
        register(self._token)
        return str(body.get("role", ""))

    def get_connection_config(self) -> dict:
        body = self._call("GET", "/openai/config")
        return normalize_openai(body if isinstance(body, dict) else {})

    def update_connection_config(self, config: dict) -> dict:
        # All four fields, always: a missing ENABLE_OPENAI_API is stored as null and silently
        # disables every OpenAI connection (findings §2.2).
        body = {k: config[k] for k in OPENAI_FIELDS}
        return normalize_openai(self._call("POST", "/openai/config/update", body))  # type: ignore[arg-type]

    def get_task_config(self) -> dict:
        body = self._call("GET", "/api/v1/tasks/config")
        return dict(body) if isinstance(body, dict) else {}

    def update_task_config(self, config: dict) -> dict:
        # The whole object: a partial body is a 422 (findings §4).
        body = self._call("POST", "/api/v1/tasks/config/update", config)
        return dict(body) if isinstance(body, dict) else {}

    def list_models(self) -> list[dict]:
        body = self._call("GET", "/api/models")
        data = body.get("data") if isinstance(body, dict) else body
        return [m for m in data or [] if isinstance(m, dict)]


def normalize_openai(cfg: dict) -> dict:
    urls = list(cfg.get("OPENAI_API_BASE_URLS") or [])
    keys = list(cfg.get("OPENAI_API_KEYS") or [])
    keys = (keys + [""] * len(urls))[: len(urls)]
    configs = cfg.get("OPENAI_API_CONFIGS") or {}
    return {
        "ENABLE_OPENAI_API": cfg.get("ENABLE_OPENAI_API"),
        "OPENAI_API_BASE_URLS": urls,
        "OPENAI_API_KEYS": keys,
        "OPENAI_API_CONFIGS": {str(k): v for k, v in configs.items()},
    }


def is_local_model(m: dict) -> bool:
    return m.get("connection_type") == "local" or m.get("owned_by") == "ollama"
