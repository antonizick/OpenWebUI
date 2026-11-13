"""apply -> no-op apply -> remove on the throwaway Open WebUI v0.13.3 testbed (ADR-0007).

Runs only with OWH_TESTBED=1 (`make test-testbed`). Creates the testbed with
scripts/owh-testbed.sh, uses a fake OpenRouter on the host (reachable from the container
because of host networking, ADR-0011), and always removes the testbed at the end.
"""

from __future__ import annotations

import getpass
import json
import os
import subprocess
from pathlib import Path

import pytest

from owh_openrouter import cli, net
from tests.fakes.server import FAKE_KEY, FakeOpenRouter

pytestmark = [
    pytest.mark.testbed,
    pytest.mark.skipif(os.environ.get("OWH_TESTBED") != "1", reason="set OWH_TESTBED=1"),
]

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "owh-testbed.sh"
URL = "http://127.0.0.1:18080"
CONTAINER = "owh-test-owu"
ADMIN = "owh-test@localhost"
PASS_FILE = (
    Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state")
    / "owh"
    / "testbed"
    / "admin-password"
)
ROWS_SQL = (
    "import json, sqlite3; "
    "c = sqlite3.connect('file:/app/backend/data/webui.db?mode=ro', uri=True); "
    "print(json.dumps(c.execute('SELECT key, value FROM config ORDER BY key').fetchall()))"
)


def run_testbed(cmd: str) -> None:
    subprocess.run([str(SCRIPT), cmd], check=True, timeout=300)


def config_rows() -> dict[str, str]:
    """`key -> value` of every row of the `config` table (`updated_at` always changes)."""
    out = subprocess.run(
        ["docker", "exec", CONTAINER, "python3", "-c", ROWS_SQL],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    ).stdout
    return dict(json.loads(out))


@pytest.fixture(scope="module")
def bed():
    exists = subprocess.run(
        ["docker", "container", "inspect", CONTAINER], capture_output=True
    ).returncode
    if exists == 0:
        pytest.fail(f"{CONTAINER} already exists; run `scripts/owh-testbed.sh down` first")
    try:
        run_testbed("up")
        yield
    finally:
        run_testbed("down")


def test_apply_noop_remove_on_the_testbed(bed, tmp_path, monkeypatch, capsys):
    password = PASS_FILE.read_text().strip()
    monkeypatch.setattr(getpass, "getpass", lambda prompt="": password)
    config = tmp_path / "config"
    config.mkdir(mode=0o700)
    (config / "openrouter.key").write_text(FAKE_KEY + "\n")
    (config / "openrouter.key").chmod(0o600)
    allow = tmp_path / "models.txt"
    allow.write_text("vendor/model-a\nvendor/model-b:free\n")

    with FakeOpenRouter() as orr:
        base = [
            "--webui-url",
            URL,
            "--openrouter-url",
            orr.url + "/api/v1",
            "--state-dir",
            str(tmp_path / "state"),
            "--config-dir",
            str(config),
        ]

        def run(*args: str) -> tuple[int, str]:
            code = cli.main([*base, *args])
            cap = capsys.readouterr()
            return code, cap.out + cap.err

        rows_before = config_rows()

        code, out = run("apply", "--email", ADMIN, "--allowlist", str(allow))
        assert code == 0, out
        rows_applied = config_rows()
        assert json.loads(rows_applied["openai.api_base_urls"]) == [orr.url + "/api/v1"]
        conf = json.loads(rows_applied["openai.api_configs"])["0"]
        assert conf["prefix_id"] == "OR" and conf["model_ids"] == [
            "vendor/model-a",
            "vendor/model-b:free",
        ]
        assert json.loads(rows_applied["openai.enable"]) is True

        # The picker list: prefixed OpenRouter models next to the local Ollama ones.
        token = net.request(
            "POST", URL + "/api/v1/auths/signin", body={"email": ADMIN, "password": password}
        )["token"]
        models = net.request("GET", URL + "/api/models", token=token)["data"]
        ids = {m["id"] for m in models}
        assert {"OR.vendor/model-a", "OR.vendor/model-b:free"} <= ids
        local = [m["id"] for m in models if m.get("owned_by") == "ollama"]
        assert local, "expected the local Ollama models next to the OpenRouter ones"

        # A chat through the prefixed model reaches the fake, with the prefix stripped.
        reply = net.request(
            "POST",
            URL + "/api/chat/completions",
            token=token,
            body={
                "model": "OR.vendor/model-a",
                "messages": [{"role": "user", "content": "hi"}],
                "stream": False,
            },
            timeout=60,
        )
        assert reply["choices"][0]["message"]["content"] == "hello from the fake"
        chats = [r for r in orr.requests if r["path"] == "/api/v1/chat/completions"]
        assert len(chats) == 1
        assert json.loads(chats[0]["body"])["model"] == "vendor/model-a"
        assert chats[0]["headers"]["Authorization"] == f"Bearer {FAKE_KEY}"

        code, out = run("status", "--json", "--email", ADMIN)
        assert code == 0, out
        report = json.loads(out)
        assert report["connections"][0]["matches_key_file"] is True
        assert report["models_listed"]["openrouter"] == 2

        code, out = run("apply", "--email", ADMIN, "--allowlist", str(allow))
        assert code == 0 and "already up to date" in out, out
        assert config_rows() == rows_applied

        code, out = run("remove", "--email", ADMIN)
        assert code == 0, out
        rows_removed = config_rows()
        assert rows_removed == rows_before, {
            k: (rows_before.get(k), rows_removed.get(k))
            for k in rows_before.keys() | rows_removed.keys()
            if rows_before.get(k) != rows_removed.get(k)
        }
        print(
            f"testbed: {len(rows_before)} config rows restored byte-for-byte (key, value); "
            f"{len(local)} local + 2 OR models listed; 1 chat reached the fake"
        )
