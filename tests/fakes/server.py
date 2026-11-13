"""Fake Open WebUI 0.13.3 and fake OpenRouter on http.server, for tests.

Shapes follow docs/OWH_FINDINGS.md (Phase 03): the OpenAI config update pads/truncates keys,
keeps only string-index configs and stores a missing ENABLE_OPENAI_API as null; the task
update needs every required field (422 otherwise); OpenRouter errors are
`{"error": {"code", "message"}}` and `/models` ignores auth.
"""

from __future__ import annotations

import copy
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# A well-formed key, built at runtime so no 40+ hex literal sits in the source (gitleaks).
FAKE_KEY = "sk-or-v1-" + "0" * 64
ADMIN_EMAIL = "admin@localhost"
ADMIN_PASSWORD = "fake-admin-password"
TOKEN = "fake-session-token-123"

# The 19 fields of GET /api/v1/tasks/config in v0.13.3 (routers/tasks.py TASK_CONFIG_KEYS).
TASK_CONFIG = {
    "TASK_MODEL": "",
    "TASK_MODEL_EXTERNAL": "",
    "TASK_MODEL_PARAMS": {},
    "TITLE_GENERATION_PROMPT_TEMPLATE": "",
    "IMAGE_PROMPT_GENERATION_PROMPT_TEMPLATE": "",
    "ENABLE_AUTOCOMPLETE_GENERATION": False,
    "AUTOCOMPLETE_GENERATION_INPUT_MAX_LENGTH": -1,
    "AUTOCOMPLETE_GENERATION_PROMPT_TEMPLATE": "",
    "TAGS_GENERATION_PROMPT_TEMPLATE": "",
    "FOLLOW_UP_GENERATION_PROMPT_TEMPLATE": "",
    "ENABLE_FOLLOW_UP_GENERATION": True,
    "ENABLE_TAGS_GENERATION": True,
    "ENABLE_TITLE_GENERATION": True,
    "ENABLE_SEARCH_QUERY_GENERATION": True,
    "ENABLE_RETRIEVAL_QUERY_GENERATION": True,
    "QUERY_GENERATION_PROMPT_TEMPLATE": "",
    "TOOLS_FUNCTION_CALLING_PROMPT_TEMPLATE": "",
    "ENABLE_VOICE_MODE_PROMPT": False,
    "VOICE_MODE_PROMPT_TEMPLATE": None,
}
# TaskConfigForm fields that have no default (a body without one of them is a 422).
TASK_REQUIRED = set(TASK_CONFIG) - {"TASK_MODEL_PARAMS", "AUTOCOMPLETE_GENERATION_INPUT_MAX_LENGTH"}


class FakeServer:
    """A JSON server on 127.0.0.1:0 with in-memory state and a request log."""

    def __init__(self) -> None:
        self.state: dict = {}
        self.requests: list[dict] = []  # {"method", "path", "headers", "body"}
        self.fail: dict[tuple[str, str], int] = {}  # (method, path) -> status to answer
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args: object) -> None:
                pass

            def _handle(self) -> None:
                n = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(n).decode() if n else ""
                req = {
                    "method": self.command,
                    "path": self.path,
                    "headers": dict(self.headers),
                    "body": raw,
                }
                outer.requests.append(req)
                forced = outer.fail.get((self.command, self.path))
                if forced:
                    status, payload = forced, {"detail": "forced failure"}
                else:
                    status, payload = outer.route(
                        self.command, self.path, json.loads(raw) if raw else None, req
                    )
                data = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            do_GET = do_POST = _handle

        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, args=(0.05,), daemon=True)

    def route(self, method: str, path: str, body, req: dict) -> tuple[int, object]:
        return 404, {"detail": "Not Found"}

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

    def paths_with(self, needle: str) -> set[str]:
        """The (method, path) of every logged request that contains `needle`."""
        return {f"{r['method']} {r['path']}" for r in self.requests if needle in json.dumps(r)}

    def writes(self) -> list[str]:
        return [r["path"] for r in self.requests if r["method"] == "POST"]


class FakeOpenRouter(FakeServer):
    """Serves `/api/v1/key`, `/api/v1/models` and `/api/v1/chat/completions`."""

    def __init__(self, valid_key: str = FAKE_KEY) -> None:
        super().__init__()
        self.valid_key = valid_key
        self.key_status = 200  # set to 402/429 to simulate those answers
        self.models = [
            {
                "id": "vendor/model-a",
                "name": "Vendor: Model A",
                "context_length": 1_000_000,
                "pricing": {"prompt": "0.000002", "completion": "0.00001"},
            },
            {
                "id": "vendor/model-b:free",
                "name": "Vendor: Model B (free)",
                "context_length": 262_144,
                "pricing": {"prompt": "0", "completion": "0"},
            },
            {
                "id": "openrouter/auto",
                "name": "Auto Router",
                "context_length": 2_000_000,
                "pricing": {"prompt": "-1", "completion": "-1"},
            },
        ]

    @staticmethod
    def _err(code: int, message: str) -> tuple[int, dict]:
        return code, {"error": {"code": code, "message": message}}

    def route(self, method, path, body, req):
        auth = req["headers"].get("Authorization", "")
        if path == "/api/v1/key" and method == "GET":
            if not auth:
                return self._err(401, "No cookie auth credentials found")
            if auth != f"Bearer {self.valid_key}":
                return self._err(401, "User not found.")
            if self.key_status != 200:
                return self._err(self.key_status, "simulated")
            return 200, {
                "data": {
                    "label": "owh-test",
                    "limit": 20,
                    "limit_remaining": 19.5,
                    "limit_reset": "monthly",
                    "usage": 0.5,
                }
            }
        if path == "/api/v1/models" and method == "GET":
            return 200, {"data": self.models, "total_count": len(self.models)}
        if path == "/api/v1/chat/completions" and method == "POST":
            if auth != f"Bearer {self.valid_key}":
                return self._err(401, "User not found.")
            return 200, {
                "id": "gen-fake",
                "object": "chat.completion",
                "created": 0,
                "model": body.get("model"),
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "hello from the fake"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 1, "completion_tokens": 4, "total_tokens": 5},
            }
        return 404, {"error": {"code": 404, "message": "Not Found"}}


class FakeOpenWebUI(FakeServer):
    """The admin endpoints OWH uses, with v0.13.3's quirks (findings §2, §4)."""

    def __init__(self) -> None:
        super().__init__()
        self.email, self.password, self.role = ADMIN_EMAIL, ADMIN_PASSWORD, "admin"
        self.local_models = ["qwen3:4b-instruct", "qwen3:8b", "gemma2:9b"]
        self.state = {
            # Pristine: the dead default entry, as on the live instance (findings §1, §2.5).
            "openai": {
                "ENABLE_OPENAI_API": True,
                "OPENAI_API_BASE_URLS": ["https://api.openai.com/v1"],
                "OPENAI_API_KEYS": [""],
                "OPENAI_API_CONFIGS": {},
            },
            "tasks": copy.deepcopy(TASK_CONFIG),
        }

    def _authed(self, req: dict) -> bool:
        return req["headers"].get("Authorization") == f"Bearer {TOKEN}"

    def _openai_models(self) -> list[dict]:
        o = self.state["openai"]
        if not o["ENABLE_OPENAI_API"]:
            return []
        out = []
        for i, _url in enumerate(o["OPENAI_API_BASE_URLS"]):
            c = o["OPENAI_API_CONFIGS"].get(str(i), {})
            if not c.get("enable", True):
                continue
            pre = c.get("prefix_id")
            for mid in c.get("model_ids") or []:
                full = f"{pre}.{mid}" if pre else mid
                out.append({"id": full, "name": full, "owned_by": "openai", "urlIdx": i})
        return out

    def route(self, method, path, body, req):
        if path == "/api/version" and method == "GET":
            return 200, {"version": "0.13.3"}
        if path == "/api/v1/auths/signin" and method == "POST":
            if (body or {}).get("email") == self.email and body.get("password") == self.password:
                return 200, {"token": TOKEN, "token_type": "Bearer", "role": self.role}
            return 400, {"detail": "The email or password provided is incorrect."}
        if not self._authed(req):
            return 401, {"detail": "Not authenticated"}
        if path == "/openai/config" and method == "GET":
            return 200, self.state["openai"]
        if path == "/openai/config/update" and method == "POST":
            urls = body["OPENAI_API_BASE_URLS"]
            keys = (body["OPENAI_API_KEYS"] + [""] * len(urls))[: len(urls)]
            valid = {str(i) for i in range(len(urls))}
            configs = {k: v for k, v in body["OPENAI_API_CONFIGS"].items() if k in valid}
            self.state["openai"] = {
                "ENABLE_OPENAI_API": body.get("ENABLE_OPENAI_API"),  # missing -> null
                "OPENAI_API_BASE_URLS": urls,
                "OPENAI_API_KEYS": keys,
                "OPENAI_API_CONFIGS": configs,
            }
            return 200, self.state["openai"]
        if path == "/api/v1/tasks/config" and method == "GET":
            return 200, self.state["tasks"]
        if path == "/api/v1/tasks/config/update" and method == "POST":
            missing = sorted(TASK_REQUIRED - set(body or {}))
            if missing:
                return 422, {
                    "detail": [{"loc": ["body", f], "msg": "Field required"} for f in missing]
                }
            data = {k: body.get(k, TASK_CONFIG[k]) for k in TASK_CONFIG}
            if data["AUTOCOMPLETE_GENERATION_INPUT_MAX_LENGTH"] is None:
                data["AUTOCOMPLETE_GENERATION_INPUT_MAX_LENGTH"] = -1
            self.state["tasks"] = data
            return 200, data
        if path == "/api/models" and method == "GET":
            local = [
                {"id": m, "name": m, "owned_by": "ollama", "connection_type": "local"}
                for m in self.local_models
            ]
            return 200, {"data": self._openai_models() + local}
        return 404, {"detail": "Not Found"}
