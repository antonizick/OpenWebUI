import stat

import pytest

from owh_openrouter import secrets
from owh_openrouter.paths import PermissionProblem

KEY = "sk-or-v1-TESTKEY" + "0" * 20


def test_redact_shows_first_nine_and_length_only():
    out = secrets.redact(KEY)
    assert out.startswith("sk-or-v1-")
    assert KEY[9:] not in out
    assert str(len(KEY)) in out


def test_write_creates_0700_dir_and_0600_file(tmp_path):
    f = tmp_path / "owh" / "openrouter.key"
    secrets.write_key(f, KEY)
    assert stat.S_IMODE(f.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(f.stat().st_mode) == 0o600
    assert secrets.read_key(f) == KEY


def test_read_accepts_0600(tmp_path):
    f = tmp_path / "k"
    f.write_text(KEY + "\n")
    f.chmod(0o600)
    assert secrets.read_key(f) == KEY


@pytest.mark.parametrize("mode", [0o644, 0o640, 0o604, 0o666])
def test_read_refuses_group_or_world_access(tmp_path, mode):
    f = tmp_path / "k"
    f.write_text(KEY)
    f.chmod(mode)
    with pytest.raises(PermissionProblem):
        secrets.read_key(f)


def test_read_refuses_empty(tmp_path):
    f = tmp_path / "k"
    f.write_text("\n")
    f.chmod(0o600)
    with pytest.raises(PermissionProblem):
        secrets.read_key(f)
