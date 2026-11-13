"""OpenRouter client: key check (`GET /key`, ADR-0013) and the public model list."""

from __future__ import annotations

from . import net

DEFAULT_URL = "https://openrouter.ai/api/v1"  # docs/OWH_FINDINGS.md §6

# HTTP status of `GET /key` -> what it means (findings §6).
KEY_ERRORS = {
    401: "key rejected (invalid, disabled or revoked)",
    402: "out of credit or the key's spending limit is reached",
    429: "rate limited; try again shortly",
}


class KeyRejected(Exception):
    def __init__(self, status: int, detail: str) -> None:
        self.status = status
        super().__init__(f"{KEY_ERRORS.get(status, f'HTTP {status}')} ({detail})")


class OpenRouter:
    def __init__(self, base_url: str, key: str | None = None, timeout: float = 15.0) -> None:
        self.base_url = base_url.rstrip("/")
        self._key = key
        self.timeout = timeout

    def key_info(self) -> dict:
        """The key's `data` object (label, limit, usage…). Raises KeyRejected on 401/402/429."""
        if not self._key:
            raise ValueError("no key")
        try:
            body = net.request("GET", self.base_url + "/key", token=self._key, timeout=self.timeout)
        except net.HttpError as e:
            if e.status in KEY_ERRORS:
                raise KeyRejected(e.status, e.detail) from None
            raise
        data = body.get("data") if isinstance(body, dict) else None
        return data if isinstance(data, dict) else {}

    def list_models(self) -> list[dict]:
        """All models. Public: sent without the key, since `/models` ignores it anyway."""
        body = net.request("GET", self.base_url + "/models", timeout=self.timeout)
        data = body.get("data") if isinstance(body, dict) else None
        return [m for m in data or [] if isinstance(m, dict) and isinstance(m.get("id"), str)]


def per_million(price: object) -> str:
    """Format an OpenRouter per-token USD price string as $ per million tokens."""
    try:
        v = float(price)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "?"
    if v < 0:
        return "variable"
    if v == 0:
        return "free"
    text = f"{v * 1e6:.3f}".rstrip("0")  # 0.435 stays 0.435, 2.000 becomes 2.00
    return text + "0" * (2 - len(text.split(".")[1]))
