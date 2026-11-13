"""Every command against the fakes, including the error paths and exit codes."""

import io
import json
import stat

import pytest

from tests.fakes.server import ADMIN_PASSWORD, FAKE_KEY, TASK_CONFIG, TOKEN, FakeOpenWebUI

OTHER_KEY = "sk-or-v1-" + "a" * 64
PRISTINE = {
    "ENABLE_OPENAI_API": True,
    "OPENAI_API_BASE_URLS": ["https://api.openai.com/v1"],
    "OPENAI_API_KEYS": [""],
    "OPENAI_API_CONFIGS": {},
}


# --- set-key -----------------------------------------------------------------------------


def test_set_key_from_prompt_stores_0600_and_prints_redacted(env):
    assert env.run("set-key") == 0
    assert env.key_file.read_text() == FAKE_KEY + "\n"
    assert stat.S_IMODE(env.key_file.stat().st_mode) == 0o600
    assert stat.S_IMODE(env.config.stat().st_mode) == 0o700
    assert "sk-or-v1-… (73 chars)" in env.out
    assert "label: owh-test" in env.out and "limit: 20" in env.out
    assert "set-key ok key=sk-or-v1- stored" in env.log
    assert not list(env.config.glob(".openrouter.key.*"))  # temp file renamed away


@pytest.mark.parametrize("command", ["set-key", "status"])
@pytest.mark.parametrize("failure", ["no-echo-control", "eof"])
def test_hidden_prompt_without_terminal_refuses_cleanly(env, monkeypatch, command, failure):
    # What Claude Code's "!" does: getpass cannot hide input, or stdin is closed.
    import getpass
    import warnings

    def no_tty(prompt=""):
        if failure == "eof":
            raise EOFError
        warnings.warn("Can not control echo on the terminal.", getpass.GetPassWarning, stacklevel=2)
        return FAKE_KEY  # the echoing fallback must never be reached

    monkeypatch.setattr(getpass, "getpass", no_tty)
    assert env.run(command) == 3
    assert "no terminal for the hidden prompt" in env.err
    assert "Traceback" not in env.err
    assert not env.key_file.exists()


def test_set_key_trims_whitespace(env):
    env.answers["OpenRouter key"] = f"  {FAKE_KEY}\n"
    assert env.run("set-key") == 0
    assert env.key_file.read_text() == FAKE_KEY + "\n"


@pytest.mark.parametrize(
    "bad",
    [
        "sk-or-v1-TESTKEY0000",  # the gitleaks-allowlisted test shape fails the format check
        "sk-or-v1-" + "0" * 63,
        "sk-or-v1-" + "G" * 64,
        "\x1b[A" + FAKE_KEY,  # arrow-key escape from a terminal
        FAKE_KEY[:20] + "\x00" + FAKE_KEY[21:],
    ],
)
def test_set_key_bad_format_is_exit_1_and_writes_nothing(env, bad):
    env.answers["OpenRouter key"] = bad
    assert env.run("set-key") == 1
    assert not env.key_file.exists()
    assert not env.orr.requests  # no network call for a malformed key


def test_set_key_rejected_key_is_exit_1(env):
    env.answers["OpenRouter key"] = OTHER_KEY
    assert env.run("set-key") == 1
    assert "key rejected" in env.err
    assert not env.key_file.exists()


@pytest.mark.parametrize(("status", "text"), [(402, "credit"), (429, "rate limited")])
def test_set_key_402_and_429_are_explained(env, status, text):
    env.orr.key_status = status
    assert env.run("set-key") == 1
    assert text in env.err


def test_set_key_openrouter_unreachable_is_exit_4(env):
    code = env.run("--openrouter-url", "http://127.0.0.1:1/api/v1", "set-key")
    assert code == 4 and not env.key_file.exists()


def test_set_key_from_file(env, tmp_path):
    src = tmp_path / "k"
    src.write_text(FAKE_KEY)
    src.chmod(0o644)
    assert env.run("set-key", "--from-file", str(src)) == 3
    src.chmod(0o600)
    assert env.run("set-key", "--from-file", str(src)) == 0
    assert env.run("set-key", "--from-file", str(tmp_path / "missing")) == 1


def test_set_key_refuses_to_overwrite_without_force(env):
    env.store_key(FAKE_KEY)
    env.orr.valid_key = OTHER_KEY
    env.answers["OpenRouter key"] = OTHER_KEY
    assert env.run("set-key") == 3  # the confirmation prompt gets EOF
    assert env.key_file.read_text().strip() == FAKE_KEY
    env.answers["Replace the stored key"] = "y"
    assert env.run("set-key") == 0
    assert env.key_file.read_text().strip() == OTHER_KEY


def test_set_key_force_and_same_key(env):
    env.store_key(OTHER_KEY)
    assert env.run("set-key", "--force") == 0
    assert env.key_file.read_text().strip() == FAKE_KEY
    assert env.run("set-key") == 0
    assert "already stored" in env.out


# --- models ------------------------------------------------------------------------------


def test_models_table_with_prices(env):
    assert env.run("models") == 0
    assert "vendor/model-a" in env.out and "2.00" in env.out and "10.00" in env.out
    assert "1,000,000" in env.out and "free" in env.out


def test_models_unknown_id_is_exit_1(env):
    env.allowlist.write_text("vendor/model-a\nvendor/gone\n")
    assert env.run("models") == 1
    assert "vendor/gone" in env.err


def test_models_json(env):
    assert env.run("models", "--json") == 0
    data = json.loads(env.out)
    assert [m["id"] for m in data["models"]] == ["vendor/model-a", "vendor/model-b:free"]
    assert data["unknown"] == []


def test_models_search_marks_allowlisted(env):
    assert env.run("models", "--allowlist", str(env.allowlist), "--search", "AUTO") == 0
    assert "openrouter/auto" in env.out and "variable" in env.out
    assert env.run("models", "--allowlist", str(env.allowlist), "--search", "model") == 0
    assert "* = on the allowlist" in env.out
    assert env.run("models", "--search", "zzz") == 0
    assert "no model matches" in env.out
    assert env.run("--json", "models", "--search", "model-b") == 0
    assert json.loads(env.out)[0]["id"] == "vendor/model-b:free"


@pytest.mark.parametrize("text", ["# nothing\n", "bad id\n"])
def test_models_empty_or_bad_allowlist_is_exit_1(env, text):
    env.allowlist.write_text(text)
    assert env.run("models") == 1


def test_models_missing_allowlist(env, tmp_path):
    assert env.run("models", "--allowlist", str(tmp_path / "none.txt")) == 1


def test_models_openrouter_down_is_exit_4(env):
    assert env.run("--openrouter-url", "http://127.0.0.1:1/api/v1", "models") == 4


# --- apply -------------------------------------------------------------------------------


def test_apply_writes_connection_task_model_and_snapshot(env):
    env.store_key()
    assert env.run("apply") == 0
    o = env.ui.state["openai"]
    assert o["ENABLE_OPENAI_API"] is True
    assert o["OPENAI_API_BASE_URLS"] == [env.orr.url + "/api/v1"]
    assert o["OPENAI_API_KEYS"] == [FAKE_KEY]
    assert o["OPENAI_API_CONFIGS"]["0"] == {
        "enable": True,
        "prefix_id": "OR",
        "connection_type": "external",
        "model_ids": ["vendor/model-a", "vendor/model-b:free"],
    }
    assert env.ui.state["tasks"]["TASK_MODEL_EXTERNAL"] == "qwen3:4b-instruct"
    snaps = env.snapshots()
    assert len(snaps) == 1 and stat.S_IMODE(snaps[0].stat().st_mode) == 0o600
    s = env.snapshot()
    assert s["before"]["openai"] == PRISTINE and s["before"]["tasks"] == TASK_CONFIG
    assert (s["slot"], s["mode"]) == (0, "replace")
    assert s["webui_url"] == env.ui.url
    assert "replaces the unused" in env.out and "applied" in env.out
    assert "apply ok key=sk-or-v1- replace slot=0 models=2" in env.log


def test_apply_twice_is_a_no_op(env):
    env.store_key()
    assert env.run("apply") == 0
    n_writes = len(env.ui.writes())
    assert env.run("apply") == 0
    assert "already up to date" in env.out
    assert env.ui.writes()[n_writes:] == ["/api/v1/auths/signin"]
    assert len(env.snapshots()) == 1


def test_apply_dry_run_writes_nothing(env):
    env.store_key()
    assert env.run("apply", "--dry-run") == 0
    assert "dry run" in env.out and "~ connection[0].url" in env.out
    assert env.ui.writes() == ["/api/v1/auths/signin"]
    assert env.ui.state["openai"] == PRISTINE
    assert not env.snapshots()


def test_apply_allowlist_change_updates_in_place(env):
    env.store_key()
    env.run("apply")
    env.allowlist.write_text("vendor/model-a\n")
    assert env.run("apply") == 0
    assert env.ui.state["openai"]["OPENAI_API_CONFIGS"]["0"]["model_ids"] == ["vendor/model-a"]
    assert env.snapshot(1)["mode"] == "update"


def test_apply_appends_next_to_a_real_connection(env):
    env.store_key()
    env.ui.state["openai"]["OPENAI_API_KEYS"] = ["sk-proj-real"]
    assert env.run("apply") == 0
    assert env.ui.state["openai"]["OPENAI_API_BASE_URLS"][0] == "https://api.openai.com/v1"
    assert env.ui.state["openai"]["OPENAI_API_KEYS"][0] == "sk-proj-real"
    assert "appended" in env.out


def test_apply_without_local_task_model_warns_and_keeps_tasks(env):
    env.store_key()
    env.ui.local_models = ["gemma2:9b"]
    assert env.run("apply") == 0
    assert "warning: neither" in env.out
    assert env.ui.state["tasks"] == TASK_CONFIG


def test_apply_explicit_task_model(env):
    env.store_key()
    assert env.run("apply", "--task-model", "qwen3:8b") == 0
    assert env.ui.state["tasks"]["TASK_MODEL_EXTERNAL"] == "qwen3:8b"


def test_apply_password_from_stdin(env, monkeypatch):
    env.store_key()
    monkeypatch.setattr("sys.stdin", io.StringIO(ADMIN_PASSWORD + "\n"))
    env.answers.pop("password")
    assert env.run("apply", "--password-stdin") == 0


def test_apply_asks_for_the_email(env):
    env.store_key()
    env.answers["admin e-mail"] = "admin@localhost"
    assert env.run("apply", "--dry-run", login=False) == 0
    env.answers["admin e-mail"] = ""
    assert env.run("apply", "--dry-run", login=False) == 1


def test_apply_wrong_password_is_exit_4(env):
    env.store_key()
    env.answers["password"] = "not-the-password-1"
    assert env.run("apply") == 4
    assert "wrong e-mail or password" in env.err
    assert env.ui.state["openai"] == PRISTINE


def test_apply_empty_password_is_exit_1(env):
    env.store_key()
    env.answers["password"] = ""
    assert env.run("apply") == 1


def test_apply_non_admin_is_refused(env):
    env.store_key()
    env.ui.role = "user"
    assert env.run("apply") == 3


def test_apply_unreachable_webui_is_exit_4(env):
    env.store_key()
    assert env.run("--webui-url", "http://127.0.0.1:1", "apply") == 4
    assert "not answering" in env.err


def test_apply_remote_webui_refused(env):
    env.store_key()
    assert env.run("--webui-url", "http://192.0.2.1:8080", "apply") == 3
    assert "--allow-remote" in env.err
    assert not env.orr.requests


def test_apply_plain_http_openrouter_refused(env):
    env.store_key()
    assert env.run("--openrouter-url", "http://openrouter.example/api/v1", "apply") == 3


def test_apply_unknown_model_is_exit_1(env):
    env.store_key()
    env.allowlist.write_text("vendor/model-a\nvendor/gone\n")
    assert env.run("apply") == 1
    assert "vendor/gone" in env.err and not env.ui.requests


def test_apply_empty_allowlist_is_exit_1(env):
    env.store_key()
    env.allowlist.write_text("\n")
    assert env.run("apply") == 1
    assert "empty" in env.err


def test_apply_without_key_file_is_exit_1(env):
    assert env.run("apply") == 1
    assert "set-key" in env.err


def test_apply_with_open_key_file_is_refused(env):
    env.store_key()
    env.key_file.chmod(0o644)
    assert env.run("apply") == 3
    assert "chmod 600" in env.err


def test_apply_with_revoked_key_is_exit_1(env):
    env.store_key(OTHER_KEY)
    assert env.run("apply") == 1
    assert not env.ui.requests


def test_apply_first_write_fails_snapshot_exists_nothing_changed(env):
    env.store_key()
    env.ui.fail[("POST", "/openai/config/update")] = 500
    assert env.run("apply") == 4
    assert "nothing changed" in env.err
    assert len(env.snapshots()) == 1  # written before the first write
    assert env.ui.state["openai"] == PRISTINE


def test_apply_partial_failure_is_exit_5(env):
    env.store_key()
    env.ui.fail[("POST", "/api/v1/tasks/config/update")] = 500
    assert env.run("apply") == 5
    assert "owh-openrouter remove" in env.err
    assert env.ui.state["openai"]["OPENAI_API_KEYS"] == [FAKE_KEY]
    # ...and remove repairs it.
    env.ui.fail.clear()
    assert env.run("remove") == 0
    assert env.ui.state["openai"] == PRISTINE


def test_apply_verify_mismatch_is_exit_5(env, monkeypatch):
    env.store_key()
    orig = env.ui.route

    def lying(method, path, body, req):
        status, payload = orig(method, path, body, req)
        if path == "/openai/config/update":
            env.ui.state["openai"] = json.loads(json.dumps(PRISTINE))  # silently not stored
        return status, payload

    env.ui.route = lying
    assert env.run("apply") == 5


def test_apply_read_failure_is_exit_4(env):
    env.store_key()
    env.ui.fail[("GET", "/api/v1/tasks/config")] = 500
    assert env.run("apply") == 4


# --- status ------------------------------------------------------------------------------


def test_status_after_apply(env):
    env.store_key()
    env.run("apply")
    assert env.run("status") == 0
    assert "Open WebUI 0.13.3" in env.out
    assert "prefix OR, 2 allowlisted" in env.out and "= key file" in env.out
    assert "'qwen3:4b-instruct' (local)" in env.out
    assert "2 OpenRouter, 3 local" in env.out
    assert "snapshots: 1" in env.out
    assert FAKE_KEY not in env.out


def test_status_json(env):
    env.store_key()
    env.run("apply")
    assert env.run("status", "--json") == 0
    r = json.loads(env.out)
    assert r["connections"][0]["matches_key_file"] is True
    assert r["connections"][0]["model_ids"] == 2
    assert r["models_listed"] == {"openrouter": 2, "local": 3, "total": 5}
    assert r["openrouter_key"]["limit"] == 20
    assert r["task_model"]["external_is_local"] is True


def test_status_before_apply_and_without_login(env):
    assert env.run("status", "--no-login") == 0
    assert "key file: none" in env.out and "snapshots: 0" in env.out
    assert not env.ui.writes()  # no sign-in


def test_status_unreachable_is_exit_4(env):
    assert env.run("--webui-url", "http://127.0.0.1:1", "status") == 4
    assert "unreachable" in env.out


def test_status_reports_key_problems_without_failing(env):
    env.store_key(OTHER_KEY)
    assert env.run("status", "--json") == 0
    assert "rejected" in json.loads(env.out)["openrouter_key"]["error"]
    env.key_file.chmod(0o644)
    assert env.run("status", "--no-login") == 0
    assert "chmod 600" in env.out


def test_status_read_failure_is_exit_4(env):
    env.ui.fail[("GET", "/openai/config")] = 500
    assert env.run("status") == 4


# --- remove ------------------------------------------------------------------------------


def test_remove_restores_exactly_and_keeps_snapshot(env):
    env.store_key()
    env.run("apply")
    assert env.run("remove") == 0
    assert env.ui.state["openai"] == PRISTINE
    assert env.ui.state["tasks"] == TASK_CONFIG
    assert len(env.snapshots()) == 1 and env.key_file.exists()
    assert "restored" in env.out
    assert env.run("remove") == 0
    assert "nothing to restore" in env.out


def test_remove_uses_the_earliest_snapshot(env):
    env.store_key()
    env.run("apply")
    env.allowlist.write_text("vendor/model-a\n")
    env.run("apply")
    assert len(env.snapshots()) == 2
    assert env.run("remove") == 0
    assert env.ui.state["openai"] == PRISTINE


def test_remove_with_a_given_snapshot_rolls_back_one_step(env):
    env.store_key()
    env.run("apply")
    env.allowlist.write_text("vendor/model-a\n")
    env.run("apply")
    assert env.run("remove", "--snapshot", str(env.snapshots()[1])) == 0
    assert env.ui.state["openai"]["OPENAI_API_CONFIGS"]["0"]["model_ids"] == [
        "vendor/model-a",
        "vendor/model-b:free",
    ]


def test_remove_ignores_snapshots_of_another_open_webui(env):
    """A testbed rehearsal shares the state dir; its snapshot must not restore live."""
    env.store_key()
    env.run("apply")
    with FakeOpenWebUI() as other:
        assert env.run("--webui-url", other.url, "remove") == 3
        assert "no OWH snapshot of" in env.err
        snap = str(env.snapshots()[0])
        assert env.run("--webui-url", other.url, "remove", "--snapshot", snap) == 3
        assert "was taken of" in env.err
        assert not other.writes()
        assert env.run("--webui-url", other.url, "status", "--no-login") == 0
        assert "snapshots: 0" in env.out
    assert env.run("remove") == 0


def test_remove_without_snapshot_is_refused(env):
    assert env.run("remove") == 3
    assert not env.ui.requests


def test_remove_with_bad_snapshot_files(env, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{}")
    bad.chmod(0o600)
    assert env.run("remove", "--snapshot", str(bad)) == 1
    bad.chmod(0o644)
    assert env.run("remove", "--snapshot", str(bad)) == 3


def test_remove_delete_key(env):
    env.store_key()
    env.run("apply")
    assert env.run("remove", "--delete-key") == 0  # confirmation gets EOF
    assert env.key_file.exists() and "key file kept" in env.out
    assert env.run("remove", "--delete-key", "--yes") == 0
    assert not env.key_file.exists()


def test_remove_failures(env):
    env.store_key()
    env.run("apply")
    env.ui.fail[("POST", "/openai/config/update")] = 500
    assert env.run("remove") == 4
    env.ui.fail = {("POST", "/api/v1/tasks/config/update"): 500}
    assert env.run("remove") == 5
    env.ui.fail = {("GET", "/openai/config"): 500}
    assert env.run("remove") == 4


# --- secrets never leak ------------------------------------------------------------------


def test_no_secret_outside_the_places_it_must_go(env):
    """Full lifecycle; then look for the key, password and token everywhere."""
    assert env.run("set-key") == 0
    assert env.run("models") == 0
    assert env.run("apply", "--dry-run") == 0
    assert env.run("apply") == 0
    assert env.run("status") == 0
    assert env.run("status", "--json") == 0
    env.answers["password"] = "wrong-" + ADMIN_PASSWORD
    assert env.run("apply") == 4
    env.answers["password"] = ADMIN_PASSWORD
    assert env.run("remove") == 0

    text = "\n".join(env.all_output) + env.log
    for secret in (FAKE_KEY, FAKE_KEY[9:], ADMIN_PASSWORD, TOKEN):
        assert secret not in text

    # The key goes to Open WebUI only in the config update body, and to OpenRouter only as
    # the Authorization header of the key check.
    assert env.ui.paths_with(FAKE_KEY) == {"POST /openai/config/update"}
    assert env.orr.paths_with(FAKE_KEY) == {"GET /api/v1/key"}
    for r in env.orr.requests:
        if FAKE_KEY in json.dumps(r):
            assert r["headers"]["Authorization"] == f"Bearer {FAKE_KEY}" and not r["body"]
    assert env.ui.paths_with(ADMIN_PASSWORD) == {"POST /api/v1/auths/signin"}
    assert not env.orr.saw(ADMIN_PASSWORD) and not env.orr.saw(TOKEN)
    assert "/api/v1/auths/signin" not in {
        r["path"] for r in env.ui.requests if TOKEN in json.dumps(r)
    }
