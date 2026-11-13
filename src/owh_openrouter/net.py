"""A small JSON-over-HTTP helper: timeouts, no redirects, and error text that holds no secrets."""

from __future__ import annotations

import ipaddress
import json
import urllib.error
import urllib.parse
import urllib.request

from .errors import Refused
from .secrets import scrub

DEFAULT_TIMEOUT = 15.0
_LOOPBACK_NAMES = {"localhost"}


class HttpError(Exception):
    """A non-2xx answer. `detail` is a short, scrubbed message from the body."""

    def __init__(self, url: str, status: int, detail: str) -> None:
        self.status = status
        self.detail = detail
        super().__init__(f"HTTP {status} from {_path(url)}: {detail}")


class Unreachable(Exception):
    """No answer at all (connection refused, DNS, timeout)."""

    def __init__(self, url: str, reason: str) -> None:
        super().__init__(f"cannot reach {_origin(url)}: {scrub(reason)}")


def _origin(url: str) -> str:
    p = urllib.parse.urlsplit(url)
    return f"{p.scheme}://{p.netloc}"


def _path(url: str) -> str:
    return _origin(url) + urllib.parse.urlsplit(url).path


def is_loopback(url: str) -> bool:
    host = urllib.parse.urlsplit(url).hostname or ""
    if host in _LOOPBACK_NAMES:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def check_url(url: str, *, what: str, allow_remote: bool = False, https_unless_local=False) -> str:
    """Refuse URLs that would send a secret somewhere unexpected."""
    p = urllib.parse.urlsplit(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        raise Refused(f"{what} URL {url!r} is not an http(s) URL")
    if p.username or p.password:
        raise Refused(f"{what} URL must not contain credentials")
    local = is_loopback(url)
    if https_unless_local:
        if p.scheme != "https" and not local:
            raise Refused(f"{what} URL must use https (the key would travel in clear text)")
    elif not local and not allow_remote:
        raise Refused(
            f"{what} URL {_origin(url)} is not on this machine; pass --allow-remote if you mean it"
        )
    return url.rstrip("/")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    # A redirect could carry the Authorization header to another host; refuse it instead.
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _opener(url: str) -> urllib.request.OpenerDirector:
    handlers: list = [_NoRedirect()]
    if is_loopback(url):
        handlers.append(urllib.request.ProxyHandler({}))
    return urllib.request.build_opener(*handlers)


def _detail(raw: bytes) -> str:
    try:
        body = json.loads(raw)
    except ValueError:
        return scrub(raw.decode("utf-8", "replace")[:200].strip()) or "(no body)"
    msg = body
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict):
            msg = err.get("message", err)
        elif "detail" in body:
            msg = body["detail"]
        elif err is not None:
            msg = err
    return scrub(str(msg))[:200]


def request(
    method: str,
    url: str,
    *,
    body: object | None = None,
    token: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> object:
    """Send one request and return the decoded JSON body (None for an empty body)."""
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with _opener(url).open(req, timeout=timeout) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        raw = e.read() if e.fp else b""
        raise HttpError(url, e.code, _detail(raw)) from None
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        raise Unreachable(url, str(getattr(e, "reason", e))) from None
    if not raw:
        return None
    try:
        return json.loads(raw)
    except ValueError:
        raise HttpError(url, 200, "answer was not JSON") from None
