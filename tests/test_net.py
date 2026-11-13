import pytest

from owh_openrouter import net, openrouter, secrets
from owh_openrouter.errors import Refused
from tests.fakes.server import FAKE_KEY, FakeOpenRouter, FakeServer


@pytest.mark.parametrize(
    "url", ["http://127.0.0.1:8080", "http://localhost:8080/", "http://[::1]:8080"]
)
def test_loopback_webui_urls_accepted(url):
    assert net.check_url(url, what="Open WebUI") == url.rstrip("/")


@pytest.mark.parametrize("url", ["http://192.168.1.5:8080", "http://example.com"])
def test_remote_webui_url_refused_unless_allowed(url):
    with pytest.raises(Refused, match="--allow-remote"):
        net.check_url(url, what="Open WebUI")
    assert net.check_url(url, what="Open WebUI", allow_remote=True)


@pytest.mark.parametrize("url", ["ftp://127.0.0.1", "127.0.0.1:8080", "http://u:p@127.0.0.1"])
def test_odd_urls_refused(url):
    with pytest.raises(Refused):
        net.check_url(url, what="x", allow_remote=True)


def test_openrouter_url_needs_https_unless_local():
    with pytest.raises(Refused, match="https"):
        net.check_url("http://openrouter.ai/api/v1", what="OpenRouter", https_unless_local=True)
    assert net.check_url("https://openrouter.ai/api/v1", what="o", https_unless_local=True)
    assert net.check_url("http://127.0.0.1:1/api/v1", what="o", https_unless_local=True)


def test_unreachable_is_reported_without_path_or_secrets():
    with pytest.raises(net.Unreachable) as e:
        net.request("GET", "http://127.0.0.1:1/secret-path", token=FAKE_KEY, timeout=2)
    assert "secret-path" not in str(e.value) and FAKE_KEY not in str(e.value)


class Echo(FakeServer):
    """Answers with whatever error body the test sets, including secrets."""

    def __init__(self, status, payload):
        super().__init__()
        self.answer = (status, payload)

    def route(self, method, path, body, req):
        return self.answer


@pytest.mark.parametrize(
    "payload",
    [
        {"detail": f"bad key {FAKE_KEY}"},
        {"error": {"code": 400, "message": f"echo {FAKE_KEY}"}},
        {"error": f"echo {FAKE_KEY}"},
        [f"{FAKE_KEY}"],
    ],
)
def test_http_error_text_is_scrubbed(payload):
    with Echo(400, payload) as s, pytest.raises(net.HttpError) as e:
        net.request("GET", s.url + "/x")
    assert e.value.status == 400
    assert FAKE_KEY not in str(e.value) and FAKE_KEY[9:] not in str(e.value)


def test_registered_secret_is_scrubbed_from_error_text():
    secrets.register("hunter2-password")
    with (
        Echo(500, {"detail": "pw hunter2-password leaked"}) as s,
        pytest.raises(net.HttpError) as e,
    ):
        net.request("POST", s.url + "/x", body={"a": 1})
    assert "hunter2" not in str(e.value)


def test_redirect_is_not_followed():
    with Echo(302, {}) as s, pytest.raises(net.HttpError) as e:
        net.request("GET", s.url + "/x", token=FAKE_KEY)
    assert e.value.status == 302


def test_non_json_answers():
    class Text(FakeServer):
        def __init__(self):
            super().__init__()

    with Text() as s:
        s.route = lambda *a: (200, "ok")  # JSON string, decodes fine
        assert net.request("GET", s.url + "/x") == "ok"


def test_openrouter_key_info_and_errors():
    with FakeOpenRouter() as fake:
        api = fake.url + "/api/v1"
        assert openrouter.OpenRouter(api, FAKE_KEY).key_info()["limit"] == 20
        with pytest.raises(openrouter.KeyRejected, match="rejected"):
            openrouter.OpenRouter(api, "sk-or-v1-" + "1" * 64).key_info()
        for status, text in [(402, "credit"), (429, "rate limited")]:
            fake.key_status = status
            with pytest.raises(openrouter.KeyRejected, match=text):
                openrouter.OpenRouter(api, FAKE_KEY).key_info()
        with pytest.raises(ValueError):
            openrouter.OpenRouter(api).key_info()


def test_models_are_fetched_without_the_key():
    with FakeOpenRouter() as fake:
        ids = [m["id"] for m in openrouter.OpenRouter(fake.url + "/api/v1", FAKE_KEY).list_models()]
        assert "vendor/model-a" in ids
        assert not fake.saw(FAKE_KEY)


@pytest.mark.parametrize(
    ("price", "shown"),
    [
        ("0.000002", "2.00"),
        ("0.00001", "10.00"),
        ("0.0000001", "0.10"),
        ("0.000000435", "0.435"),
        ("0.000000038", "0.038"),
        ("0", "free"),
        ("-1", "variable"),
        (None, "?"),
    ],
)
def test_per_million(price, shown):
    assert openrouter.per_million(price) == shown


@pytest.mark.parametrize(
    ("expires_at", "expected"),
    [
        (None, None),
        ("", None),
        ("not a date", None),
        ("2027-11-13T18:03:06", None),  # no time zone: do not guess
        ("2027-11-13T18:03:06.508Z", None),  # a year away
        ("2027-11-01T00:00:00Z", "in 18 days"),
        ("2027-10-01T00:00:00Z", "expired on"),
    ],
)
def test_expiry_warning(expires_at, expected):
    from datetime import UTC, datetime

    now = datetime(2027, 10, 13, 12, 0, tzinfo=UTC)
    got = openrouter.expiry_warning(expires_at, now)
    assert (got is None) if expected is None else (expected in got)
