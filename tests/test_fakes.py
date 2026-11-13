import json
import urllib.error
import urllib.request

import pytest

from tests.fakes.server import FakeOpenRouter, FakeOpenWebUI

KEY = "sk-or-v1-TESTKEY0000"


def _get(url, key=None):
    req = urllib.request.Request(url)
    if key:
        req.add_header("Authorization", f"Bearer {key}")
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def test_fake_openrouter_answers_and_checks_key():
    with FakeOpenRouter(KEY) as fake:
        assert _get(fake.url + "/api/v1/key", KEY)["data"]["limit"] == 20
        with pytest.raises(urllib.error.HTTPError) as e:
            _get(fake.url + "/api/v1/key", "sk-or-v1-TESTKEYbad")
        assert e.value.code == 401
        assert _get(fake.url + "/api/v1/models")["data"][0]["id"] == "vendor/model-a"
        assert fake.saw(KEY)  # the request log lets tests assert where a key appears
        assert not fake.saw("never-sent")


def test_fake_openwebui_roundtrips_config():
    with FakeOpenWebUI() as fake:
        cfg = _get(fake.url + "/openai/config")
        cfg["OPENAI_API_BASE_URLS"] = ["https://openrouter.ai/api/v1"]
        req = urllib.request.Request(
            fake.url + "/openai/config/update",
            data=json.dumps(cfg).encode(),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req).read()
        assert fake.state["openai"]["OPENAI_API_BASE_URLS"] == ["https://openrouter.ai/api/v1"]
