"""Fake Open WebUI and fake OpenRouter on http.server, for tests.

Endpoint shapes are the spec's expected list (R6).
TODO(phase-04): align with docs/OWH_FINDINGS.md.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class FakeServer:
    """A JSON server on 127.0.0.1:0 with in-memory state and a request log."""

    def __init__(self) -> None:
        self.state: dict = {}
        self.requests: list[dict] = []  # {"method", "path", "headers", "body"}
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args: object) -> None:
                pass

            def _handle(self) -> None:
                n = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(n).decode() if n else ""
                outer.requests.append(
                    {
                        "method": self.command,
                        "path": self.path,
                        "headers": dict(self.headers),
                        "body": raw,
                    }
                )
                status, payload = outer.route(
                    self.command, self.path, json.loads(raw) if raw else None
                )
                data = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            do_GET = do_POST = _handle

        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)

    def route(self, method: str, path: str, body: dict | None) -> tuple[int, dict]:
        return 404, {"detail": "not found"}

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self._httpd.server_port}"

    def __enter__(self) -> FakeServer:
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()

    def saw(self, needle: str) -> bool:
        """True if `needle` appears anywhere in any logged request."""
        return any(needle in json.dumps(r) for r in self.requests)


class FakeOpenRouter(FakeServer):
    def __init__(self, valid_key: str = "sk-or-v1-TESTKEY0000") -> None:
        super().__init__()
        self.valid_key = valid_key
        self.models = [{"id": "vendor/model-a", "pricing": {"prompt": "0", "completion": "0"}}]

    def route(self, method, path, body):
        if path == "/api/v1/key":
            auth = self.requests[-1]["headers"].get("Authorization", "")
            if auth != f"Bearer {self.valid_key}":
                return 401, {"error": "invalid key"}
            return 200, {"data": {"label": "test", "limit": 20, "usage": 0}}
        if path == "/api/v1/models":
            return 200, {"data": self.models}
        return 404, {"detail": "not found"}


class FakeOpenWebUI(FakeServer):
    def __init__(self) -> None:
        super().__init__()
        self.state = {
            "openai": {
                "ENABLE_OPENAI_API": True,
                "OPENAI_API_BASE_URLS": [],
                "OPENAI_API_KEYS": [],
            },
            "tasks": {"TASK_MODEL": "", "TASK_MODEL_EXTERNAL": ""},
        }

    def route(self, method, path, body):
        if path == "/api/v1/auths/signin" and method == "POST":
            return 200, {"token": "fake-jwt", "role": "admin"}
        if path == "/openai/config" and method == "GET":
            return 200, self.state["openai"]
        if path == "/openai/config/update" and method == "POST":
            self.state["openai"] = body
            return 200, body
        if path == "/api/v1/tasks/config" and method == "GET":
            return 200, self.state["tasks"]
        if path == "/api/v1/tasks/config/update" and method == "POST":
            self.state["tasks"] = body
            return 200, body
        if path == "/api/models":
            return 200, {"data": []}
        return 404, {"detail": "not found"}
