"""Phase 06 on the throwaway testbed: upgrade survival (R2) and offline behaviour (R5).

Runs only with OWH_TESTBED=1 (`make test-testbed`). The container is recreated with the
functions of `~/.local/bin/open-webui-upgrade` itself (`make_recipe`, `create_from_recipe`),
never against the live instance. The allowlist is the real `config/openrouter-models.txt`,
served by the fake OpenRouter, so no key or money is involved.
"""

from __future__ import annotations

import getpass
import json
import os
import statistics
import subprocess
import time
from pathlib import Path

import pytest

from owh_openrouter import allowlist, cli, net, webui
from tests.fakes.server import FAKE_KEY, FakeOpenRouter
from tests.integration.test_testbed import ADMIN, CONTAINER, PASS_FILE, URL, config_rows

pytestmark = [
    pytest.mark.testbed,
    pytest.mark.skipif(os.environ.get("OWH_TESTBED") != "1", reason="set OWH_TESTBED=1"),
]

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "owh-testbed.sh"
ALLOWLIST = ROOT / "config" / "openrouter-models.txt"
UPGRADE = Path.home() / ".local" / "bin" / "open-webui-upgrade"
PREV = CONTAINER + "-prev"
LOCAL_MODEL = "qwen3:4b-instruct"
OWH_ROWS = (
    "openai.enable",
    "openai.api_base_urls",
    "openai.api_keys",
    "openai.api_configs",
    "task.model.external",
)

# Recreate CONTAINER exactly as open-webui-upgrade does: its own two functions, sourced
# from the script, on the same image (an "upgrade" to the same version).
RECREATE = r"""
set -euo pipefail
source <(sed -n '/^make_recipe() {/,/^}/p; /^create_from_recipe() {/,/^}/p' "$1")
c="$(docker inspect "$2")"
i="$(docker image inspect "$(jq -r '.[0].Image' <<<"$c")")"
recipe="$(make_recipe "$c" "$i")"
img="$(jq -r .image_ref <<<"$recipe")"
docker stop "$2" >/dev/null
docker rename "$2" "$3"
create_from_recipe "$recipe" "$img" "$2"
docker start "$2" >/dev/null
jq -c '{network, binds, env: [.env[] | split("=")[0]]}' <<<"$recipe"
"""


def wait_healthy(timeout: float = 300) -> float:
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        try:
            if net.request("GET", URL + "/health", timeout=2):
                return time.monotonic() - t0
        except (net.HttpError, net.Unreachable):
            pass
        time.sleep(1)
    pytest.fail(f"no /health from {URL} after {timeout} s")


def owh_rows() -> dict[str, str]:
    rows = config_rows()
    return {k: rows.get(k) for k in OWH_ROWS}


def timed_models(token: str, runs: int = 3) -> tuple[float, int, int]:
    """Median seconds for GET /api/models, plus the OR. and local counts of the last run."""
    times, models = [], []
    for _ in range(runs):
        time.sleep(1.2)  # the model list cache lives 1 s (findings §5)
        t0 = time.monotonic()
        models = net.request("GET", URL + "/api/models", token=token, timeout=60)["data"]
        times.append(time.monotonic() - t0)
    n_or = sum(m["id"].startswith("OR.") for m in models)
    n_local = sum(webui.is_local_model(m) for m in models)
    return statistics.median(times), n_or, n_local


@pytest.fixture(scope="module")
def bed():
    for name in (CONTAINER, PREV):
        if (
            subprocess.run(["docker", "container", "inspect", name], capture_output=True).returncode
            == 0
        ):
            pytest.fail(f"{name} already exists; run `scripts/owh-testbed.sh down` first")
    try:
        subprocess.run([str(SCRIPT), "up"], check=True, timeout=400)
        yield
    finally:
        subprocess.run(["docker", "rm", "-f", PREV], capture_output=True)
        subprocess.run([str(SCRIPT), "down"], check=True, timeout=120)


@pytest.mark.skipif(not UPGRADE.exists(), reason="open-webui-upgrade is not installed")
def test_upgrade_survival_and_offline(bed, tmp_path, monkeypatch, capsys):
    password = PASS_FILE.read_text().strip()
    monkeypatch.setattr(getpass, "getpass", lambda prompt="": password)
    config = tmp_path / "config"
    config.mkdir(mode=0o700)
    (config / "openrouter.key").write_text(FAKE_KEY + "\n")
    (config / "openrouter.key").chmod(0o600)
    ids = allowlist.load(ALLOWLIST)
    report: list[str] = []

    with FakeOpenRouter() as orr:
        orr.models = [
            {"id": i, "name": i, "pricing": {"prompt": "0", "completion": "0"}} for i in ids
        ]
        base = [
            "--webui-url", URL,
            "--openrouter-url", orr.url + "/api/v1",
            "--state-dir", str(tmp_path / "state"),
            "--config-dir", str(config),
        ]  # fmt: skip

        def run(*args: str) -> tuple[int, str]:
            code = cli.main([*base, *args])
            cap = capsys.readouterr()
            return code, cap.out + cap.err

        code, out = run("apply", "--email", ADMIN, "--allowlist", str(ALLOWLIST))
        assert code == 0, out
        code, out = run("status", "--json", "--email", ADMIN)
        assert code == 0, out
        status_before = json.loads(out)
        rows_before = owh_rows()
        started_before = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.StartedAt}} {{.Id}}", CONTAINER],
            check=True, capture_output=True, text=True,
        ).stdout.split()  # fmt: skip

        # --- R2: recreate with open-webui-upgrade's own recipe functions, same volume ---
        recipe = subprocess.run(
            ["bash", "-c", RECREATE, "recreate", str(UPGRADE), CONTAINER, PREV],
            check=True, capture_output=True, text=True, timeout=120,
        ).stdout.strip()  # fmt: skip
        health_s = wait_healthy()
        subprocess.run(["docker", "rm", "-f", PREV], check=True, capture_output=True)
        started_after = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.StartedAt}} {{.Id}}", CONTAINER],
            check=True, capture_output=True, text=True,
        ).stdout.split()  # fmt: skip
        assert started_after[1] != started_before[1], "the container was not recreated"

        assert owh_rows() == rows_before
        code, out = run("status", "--json", "--email", ADMIN)
        assert code == 0, out
        status_after = json.loads(out)
        for k in ("connections", "task_model", "models_listed", "openai_enabled"):
            assert status_after[k] == status_before[k], k
        assert status_after["models_listed"]["openrouter"] == len(ids)
        report.append(
            f"R2: recreated via open-webui-upgrade recipe {recipe}; "
            f"healthy after {health_s:.0f} s; "
            f"{len(OWH_ROWS)} OWH rows identical; status identical "
            f"({len(ids)} OR, {status_after['models_listed']['local']} local, "
            f"task model {status_after['task_model']['TASK_MODEL_EXTERNAL']!r})"
        )

        # --- R5: point the connection at dead upstreams and time the model list ---
        ui = webui.WebUI(URL, 60)
        ui.signin(ADMIN, password)
        token = ui._token
        assert token
        healthy = ui.get_connection_config()
        upstreams = {
            "fake, healthy": healthy["OPENAI_API_BASE_URLS"][0],
            "closed port 127.0.0.1:1": "http://127.0.0.1:1/api/v1",
            "unroutable 10.255.255.1": "http://10.255.255.1/api/v1",
        }
        for label, url in upstreams.items():
            cfg = json.loads(json.dumps(healthy))
            cfg["OPENAI_API_BASE_URLS"][0] = url
            ui.update_connection_config(cfg)
            secs, n_or, n_local = timed_models(token)
            assert n_or == len(ids) and n_local > 0, (label, n_or, n_local)
            assert secs < 2.0, f"{label}: /api/models took {secs:.2f} s"
            report.append(
                f"R5: {label}: /api/models median {secs:.2f} s, {n_or} OR + {n_local} local"
            )

        # Upstream unroutable: a local chat still answers.
        t0 = time.monotonic()
        reply = net.request(
            "POST",
            URL + "/api/chat/completions",
            token=token,
            body={
                "model": LOCAL_MODEL,
                "messages": [{"role": "user", "content": "Reply with the word OK."}],
                "stream": False,
            },
            timeout=180,
        )
        local_s = time.monotonic() - t0
        assert reply["choices"][0]["message"]["content"].strip()
        report.append(
            f"R5: local chat on {LOCAL_MODEL} with OpenRouter unroutable: {local_s:.2f} s"
        )

        # Closed port: an OR. chat fails fast instead of hanging.
        cfg = json.loads(json.dumps(healthy))
        cfg["OPENAI_API_BASE_URLS"][0] = upstreams["closed port 127.0.0.1:1"]
        ui.update_connection_config(cfg)
        t0 = time.monotonic()
        with pytest.raises(net.HttpError) as err:
            net.request(
                "POST",
                URL + "/api/chat/completions",
                token=token,
                body={"model": f"OR.{ids[0]}", "messages": [{"role": "user", "content": "hi"}]},
                timeout=60,
            )
        report.append(
            f"R5: OR. chat with the upstream port closed: HTTP {err.value.status} "
            f"in {time.monotonic() - t0:.2f} s ({err.value.detail})"
        )
        ui.update_connection_config(healthy)

        # Spend guard: what a chat shows when the key limit or the credit is exhausted.
        orr.chat_status = 402
        t0 = time.monotonic()
        with pytest.raises(net.HttpError) as err:
            net.request(
                "POST",
                URL + "/api/chat/completions",
                token=token,
                body={"model": f"OR.{ids[0]}", "messages": [{"role": "user", "content": "hi"}]},
                timeout=60,
            )
        report.append(
            f"402 from OpenRouter: Open WebUI answers HTTP {err.value.status} "
            f"in {time.monotonic() - t0:.2f} s with detail {err.value.detail!r}"
        )
        orr.chat_status = 200

        code, out = run("remove", "--email", ADMIN)
        assert code == 0, out

    with capsys.disabled():
        print("\n" + "\n".join(report))
