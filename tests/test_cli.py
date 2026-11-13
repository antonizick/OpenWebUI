import pytest

from owh_openrouter.cli import build_parser, main

COMMANDS = ["set-key", "models", "apply", "status", "remove"]


def test_help_lists_all_subcommands_and_exit_codes(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--help"])
    assert e.value.code == 0
    out = capsys.readouterr().out
    for c in COMMANDS:
        assert c in out
    assert "5 failed after a partial change" in out


def test_usage_error_is_exit_2(capsys):
    with pytest.raises(SystemExit) as e:
        main(["apply", "--no-such-flag"])
    assert e.value.code == 2


def test_global_defaults():
    a = build_parser().parse_args(["status"])
    assert a.webui_url == "http://127.0.0.1:8080"
    assert a.openrouter_url == "https://openrouter.ai/api/v1"
    assert a.json is False
    assert a.allow_remote is False


def test_json_after_the_subcommand_does_not_clobber_the_global_flag():
    assert build_parser().parse_args(["status", "--json"]).json is True
    assert build_parser().parse_args(["--json", "status"]).json is True


def test_apply_flags():
    a = build_parser().parse_args(["apply", "--dry-run", "--email", "a@b"])
    assert a.dry_run is True and a.email == "a@b" and a.password_stdin is False
