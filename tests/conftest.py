import getpass
import json
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from owh_openrouter import cli
from tests.fakes.server import ADMIN_EMAIL, ADMIN_PASSWORD, FAKE_KEY, FakeOpenRouter, FakeOpenWebUI


@dataclass
class Env:
    ui: FakeOpenWebUI
    orr: FakeOpenRouter
    config: Path
    state: Path
    allowlist: Path
    capsys: pytest.CaptureFixture
    monkeypatch: pytest.MonkeyPatch
    answers: dict = field(default_factory=dict)  # prompt substring -> reply
    out: str = ""
    err: str = ""
    all_output: list[str] = field(default_factory=list)

    @property
    def key_file(self) -> Path:
        return self.config / "openrouter.key"

    @property
    def log(self) -> str:
        p = self.state / "owh.log"
        return p.read_text() if p.exists() else ""

    def store_key(self, key: str = FAKE_KEY) -> None:
        self.config.mkdir(mode=0o700, exist_ok=True)
        self.key_file.write_text(key + "\n")
        self.key_file.chmod(0o600)

    def run(self, *args: str, login: bool = True) -> int:
        base = [
            "--webui-url",
            self.ui.url,
            "--openrouter-url",
            self.orr.url + "/api/v1",
            "--state-dir",
            str(self.state),
            "--config-dir",
            str(self.config),
            "--timeout",
            "5",
        ]
        i = next(i for i, a in enumerate(args) if a in cli.COMMANDS)
        pre, cmd, rest = list(args[:i]), args[i], list(args[i + 1 :])
        extra = []
        if login and cmd in ("apply", "status", "remove") and "--email" not in rest:
            extra = ["--email", ADMIN_EMAIL]
        if cmd in ("apply", "models") and "--allowlist" not in rest and "--search" not in rest:
            extra += ["--allowlist", str(self.allowlist)]
        code = cli.main([*base, *pre, cmd, *extra, *rest])
        cap = self.capsys.readouterr()
        self.out, self.err = cap.out, cap.err
        self.all_output += [cap.out, cap.err]
        return code

    def snapshots(self) -> list[Path]:
        return sorted((self.state / "snapshots").glob("*.json"))

    def snapshot(self, i: int = 0) -> dict:
        return json.loads(self.snapshots()[i].read_text())


@pytest.fixture
def env(tmp_path, capsys, monkeypatch):
    allow = tmp_path / "models.txt"
    allow.write_text("# test allowlist\nvendor/model-a\nvendor/model-b:free\n")
    with FakeOpenWebUI() as ui, FakeOpenRouter() as orr:
        e = Env(ui, orr, tmp_path / "config", tmp_path / "state", allow, capsys, monkeypatch)
        e.answers = {"password": ADMIN_PASSWORD, "OpenRouter key": FAKE_KEY}

        def fake_getpass(prompt: str = "") -> str:
            for k, v in e.answers.items():
                if k in prompt:
                    return v
            raise AssertionError(f"unexpected prompt {prompt!r}")

        def fake_input(prompt: str = "") -> str:
            for k, v in e.answers.items():
                if k in prompt:
                    return v
            raise EOFError

        monkeypatch.setattr(getpass, "getpass", fake_getpass)
        monkeypatch.setattr("builtins.input", fake_input)
        yield e
