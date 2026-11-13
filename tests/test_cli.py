import pytest

from owh_openrouter.cli import build_parser, main

COMMANDS = ["set-key", "models", "apply", "status", "remove"]


def test_help_lists_all_subcommands(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--help"])
    assert e.value.code == 0
    out = capsys.readouterr().out
    for c in COMMANDS:
        assert c in out


@pytest.mark.parametrize("cmd", COMMANDS)
def test_stubs_exit_2(cmd, capsys):
    assert main([cmd]) == 2
    assert "not implemented" in capsys.readouterr().err


def test_global_defaults():
    a = build_parser().parse_args(["status"])
    assert a.webui_url == "http://127.0.0.1:8080"
    assert a.openrouter_url == "https://openrouter.ai/api/v1"
    assert a.json is False


def test_apply_dry_run_flag():
    assert build_parser().parse_args(["apply", "--dry-run"]).dry_run is True
