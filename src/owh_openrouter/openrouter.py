"""OpenRouter client: key check (`GET /key`, ADR-0013) and the public model list."""

from __future__ import annotations

from datetime import datetime, timedelta

from . import net

DEFAULT_URL = "https://openrouter.ai/api/v1"  # docs/OWH_FINDINGS.md §6

# HTTP status of `GET /key` -> what it means (findings §6).
KEY_ERRORS = {
    401: "key rejected (invalid, disabled or revoked)",
    402: "out of credit or the key's spending limit is reached",
    429: "rate limited; try again shortly",
}


# Key-info fields worth showing. Not `label`: it is a masked key preview, not a name (§6a).
KEY_FIELDS = ("limit", "limit_remaining", "limit_reset", "usage", "usage_monthly", "expires_at")
EXPIRY_WARNING_DAYS = 30


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


def expiry_warning(expires_at: object, now: datetime | None = None) -> str | None:
    """A warning when the key has expired or expires within EXPIRY_WARNING_DAYS, else None."""
    if not isinstance(expires_at, str) or not expires_at:
        return None
    try:
        when = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    if when.tzinfo is None:
        return None
    now = now or datetime.now(when.tzinfo)
    day = when.astimezone().strftime("%Y-%m-%d")
    if when <= now:
        return f"the OpenRouter key expired on {day}; rotate it (SECURITY.md, 'Rotating the key')"
    if when - now <= timedelta(days=EXPIRY_WARNING_DAYS):
        days = (when - now).days
        return f"the OpenRouter key expires on {day} (in {days} days); rotate it before then"
    return None
