import json
import stat

import pytest

from owh_openrouter import snapshot
from owh_openrouter.paths import PermissionProblem


def test_save_is_private_and_ordered(tmp_path):
    a = snapshot.save(tmp_path, {"before": {"x": 1}, "url": "u", "slot": 0, "mode": "replace"})
    b = snapshot.save(tmp_path, {"before": {"x": 2}, "url": "u", "slot": 0, "mode": "update"})
    assert stat.S_IMODE(a.stat().st_mode) == 0o600
    assert stat.S_IMODE(a.parent.stat().st_mode) == 0o700
    assert snapshot.all_paths(tmp_path) == [a, b]
    assert snapshot.earliest(tmp_path) == a
    assert snapshot.load(a)["before"] == {"x": 1}


def test_no_snapshots(tmp_path):
    assert snapshot.earliest(tmp_path) is None


def test_load_refuses_open_permissions_and_foreign_files(tmp_path):
    f = tmp_path / "s.json"
    f.write_text(json.dumps({"version": 1, "before": {}}))
    f.chmod(0o644)
    with pytest.raises(PermissionProblem):
        snapshot.load(f)
    f.chmod(0o600)
    assert snapshot.load(f)["before"] == {}
    f.write_text("[]")
    with pytest.raises(ValueError):
        snapshot.load(f)


def test_filter_by_webui_url(tmp_path):
    live = snapshot.save(tmp_path, {"before": {}, "webui_url": "http://127.0.0.1:8080"})
    bed = snapshot.save(tmp_path, {"before": {}, "webui_url": "http://127.0.0.1:18080"})
    (tmp_path / "snapshots" / "junk.json").write_text("not json")
    assert snapshot.all_paths(tmp_path, "http://127.0.0.1:18080/") == [bed]
    assert snapshot.earliest(tmp_path, "http://127.0.0.1:8080") == live
    assert snapshot.earliest(tmp_path, "http://localhost:8080") is None
