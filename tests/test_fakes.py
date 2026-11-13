import json
import urllib.error
import urllib.request

import pytest

from tests.fakes.server import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    FAKE_KEY,
    TASK_CONFIG,
    TOKEN,
    FakeOpenRouter,
    FakeOpenWebUI,
)


def _call(url, body=None, token=None):
    req = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode())
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def _status(url, body=None, token=None):
    with pytest.raises(urllib.error.HTTPError) as e:
        _call(url, body, token)
    return e.value.code, json.load(e.value)


def test_fake_key_is_well_formed_and_73_chars():
    assert len(FAKE_KEY) == 73


def test_fake_openrouter_key_errors_use_openrouter_shape():
    with FakeOpenRouter() as fake:
        assert _call(fake.url + "/api/v1/key", token=FAKE_KEY)["data"]["limit"] == 20
        code, body = _status(fake.url + "/api/v1/key", token="sk-or-v1-TESTKEYbad")
        assert code == 401 and body == {"error": {"code": 401, "message": "User not found."}}
        assert _status(fake.url + "/api/v1/key")[0] == 401
        fake.key_status = 402
        assert _status(fake.url + "/api/v1/key", token=FAKE_KEY)[1]["error"]["code"] == 402


def test_fake_openrouter_models_ignore_auth():
    with FakeOpenRouter() as fake:
        a = _call(fake.url + "/api/v1/models")
        b = _call(fake.url + "/api/v1/models", token="sk-or-v1-TESTKEYbad")
        assert a == b and a["data"][0]["id"] == "vendor/model-a"
        assert fake.saw("TESTKEYbad") and not fake.saw("never-sent")


def test_fake_openwebui_update_quirks():
    with FakeOpenWebUI() as fake:
        tok = _call(
            fake.url + "/api/v1/auths/signin", {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert tok["token"] == TOKEN
        assert _call(fake.url + "/openai/config", token=TOKEN)["OPENAI_API_KEYS"] == [""]
        out = _call(
            fake.url + "/openai/config/update",
            {
                "OPENAI_API_BASE_URLS": ["a", "b"],
                "OPENAI_API_KEYS": ["k"],
                "OPENAI_API_CONFIGS": {"0": {}, "7": {}, "a": {}},
            },
            TOKEN,
        )
        assert out["ENABLE_OPENAI_API"] is None  # omitted -> null (findings §2.2)
        assert out["OPENAI_API_KEYS"] == ["k", ""]
        assert out["OPENAI_API_CONFIGS"] == {"0": {}}


def test_fake_openwebui_task_update_needs_full_object():
    with FakeOpenWebUI() as fake:
        assert (
            _status(fake.url + "/api/v1/tasks/config/update", {"TASK_MODEL_EXTERNAL": "x"}, TOKEN)[
                0
            ]
            == 422
        )
        full = {**TASK_CONFIG, "TASK_MODEL_EXTERNAL": "x"}
        assert _call(fake.url + "/api/v1/tasks/config/update", full, TOKEN) == full
        assert len(TASK_CONFIG) == 19


def test_fake_openwebui_needs_token_and_right_password():
    with FakeOpenWebUI() as fake:
        assert _status(fake.url + "/openai/config")[0] == 401
        assert (
            _status(fake.url + "/api/v1/auths/signin", {"email": ADMIN_EMAIL, "password": "x"})[0]
            == 400
        )
