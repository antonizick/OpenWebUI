import stat

from owh_openrouter import paths


def test_config_and_state_dirs_follow_xdg():
    env = {"XDG_CONFIG_HOME": "/x/c", "XDG_STATE_HOME": "/x/s"}
    assert str(paths.config_dir(env)) == "/x/c/owh"
    assert str(paths.state_dir(env)) == "/x/s/owh"


def test_dirs_default_under_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert paths.config_dir({}) == tmp_path / ".config" / "owh"
    assert paths.state_dir({}) == tmp_path / ".local" / "state" / "owh"


def test_ensure_private_dir_is_0700(tmp_path):
    d = paths.ensure_private_dir(tmp_path / "a" / "owh")
    assert stat.S_IMODE(d.stat().st_mode) == 0o700


def test_ensure_private_dir_tightens_existing(tmp_path):
    d = tmp_path / "owh"
    d.mkdir(mode=0o755)
    paths.ensure_private_dir(d)
    assert stat.S_IMODE(d.stat().st_mode) == 0o700
