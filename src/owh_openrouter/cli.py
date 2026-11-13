"""Command-line entry point: `owh-openrouter`.

Secrets (the OpenRouter key, the admin password, the session token) come only from a hidden
prompt, stdin or the 0600 key file, and every line printed or logged goes through `scrub`.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import warnings
from datetime import datetime
from pathlib import Path

from . import __version__, allowlist, net, openrouter, paths, plan, secrets, snapshot, webui
from .errors import OK, VALIDATION, Failed, OwhError, PartialFailure, Refused, ValidationError
from .secrets import redact, scrub

REPO_ALLOWLIST = Path(__file__).resolve().parents[2] / "config" / "openrouter-models.txt"


class Ctx:
    """Resolved options for one run, plus what the action log should say about it."""

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.config_dir = Path(args.config_dir) if args.config_dir else paths.config_dir()
        self.state_dir = Path(args.state_dir) if args.state_dir else paths.state_dir()
        self.key_path = paths.key_file(self.config_dir)
        self.key_prefix = "-"
        self.detail = ""

    @property
    def webui_url(self) -> str:
        return net.check_url(
            self.args.webui_url, what="Open WebUI", allow_remote=self.args.allow_remote
        )

    @property
    def openrouter_url(self) -> str:
        return net.check_url(self.args.openrouter_url, what="OpenRouter", https_unless_local=True)

    def allowlist_path(self) -> Path:
        return Path(getattr(self.args, "allowlist", None) or REPO_ALLOWLIST)


# --- small helpers -----------------------------------------------------------------------


def say(msg: str = "") -> None:
    print(scrub(msg))


def warn(msg: str) -> None:
    print(scrub(msg), file=sys.stderr)


def confirm(question: str, args: argparse.Namespace) -> bool:
    if getattr(args, "yes", False):
        return True
    try:
        return input(f"{question} [y/N] ").strip().lower() in ("y", "yes")
    except EOFError:
        return False


def read_secret(prompt: str, from_stdin: bool) -> str:
    if from_stdin:
        return sys.stdin.readline().rstrip("\r\n")
    # Without a terminal getpass would fall back to an echoing prompt; refuse instead.
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            return getpass.getpass(prompt)
    except (getpass.GetPassWarning, EOFError):
        raise Refused(
            "no terminal for the hidden prompt; run this in a terminal window "
            "(not through Claude Code's '!'), or use --from-file / --password-stdin"
        ) from None


def log_action(ctx: Ctx, action: str, result: str) -> None:
    try:
        paths.ensure_private_dir(ctx.state_dir)
        log = ctx.state_dir / "owh.log"
        stamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        line = f"{stamp} {action} {result} key={ctx.key_prefix} {ctx.detail}".rstrip()
        fd = os.open(log, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as fh:
            fh.write(scrub(line) + "\n")
    except OSError as e:
        warn(f"warning: could not write the action log: {e}")


def load_key(ctx: Ctx) -> str:
    if not ctx.key_path.exists():
        raise ValidationError(f"no key stored at {ctx.key_path}; run `owh-openrouter set-key`")
    try:
        key = secrets.read_key(ctx.key_path)
    except paths.PermissionProblem as e:
        raise Refused(f"{e}; fix with `chmod 600 {ctx.key_path}`") from None
    secrets.register(key)
    ctx.key_prefix = key[:9]
    return key


def load_allowlist(ctx: Ctx) -> list[str]:
    path = ctx.allowlist_path()
    try:
        ids = allowlist.load(path)
    except FileNotFoundError:
        raise ValidationError(f"allowlist {path} not found") from None
    except allowlist.AllowlistError as e:
        raise ValidationError(f"allowlist {path}: {e}") from None
    if not ids:
        raise ValidationError(
            f"allowlist {path} is empty; add at least one OpenRouter model ID "
            "(an empty list would show all ~470 models and stall the picker when offline)"
        )
    return ids


def check_key_live(ctx: Ctx, key: str) -> dict:
    try:
        return openrouter.OpenRouter(ctx.openrouter_url, key, ctx.args.timeout).key_info()
    except openrouter.KeyRejected as e:
        raise ValidationError(f"OpenRouter: {e}") from None
    except (net.HttpError, net.Unreachable) as e:
        raise Failed(f"OpenRouter key check failed: {e}") from None


def fetch_models(ctx: Ctx) -> list[dict]:
    try:
        return openrouter.OpenRouter(ctx.openrouter_url, timeout=ctx.args.timeout).list_models()
    except (net.HttpError, net.Unreachable) as e:
        raise Failed(f"OpenRouter model list: {e}") from None


def signin(ctx: Ctx) -> webui.WebUI:
    a = ctx.args
    ui = webui.WebUI(ctx.webui_url, a.timeout)
    try:
        ui.version()
    except (net.HttpError, net.Unreachable) as e:
        raise Failed(f"Open WebUI is not answering at {ui.base_url}: {e}") from None
    email = a.email
    if not email:
        try:
            email = input("Open WebUI admin e-mail: ").strip()
        except EOFError:
            email = ""
    if not email:
        raise ValidationError("no admin e-mail given (use --email)")
    password = read_secret("Open WebUI admin password (hidden): ", a.password_stdin)
    secrets.register(password)
    if not password:
        raise ValidationError("no admin password given")
    try:
        role = ui.signin(email, password)
    except net.HttpError as e:
        if e.status in (400, 401, 403):
            raise Failed("Open WebUI sign-in failed: wrong e-mail or password") from None
        raise Failed(f"Open WebUI sign-in failed: {e}") from None
    if role != "admin":
        raise Refused(f"{email} is not an Open WebUI admin (role {role!r})")
    return ui


def model_row(m: dict) -> dict:
    p = m.get("pricing") or {}
    return {
        "id": m["id"],
        "name": str(m.get("name", "")),
        "context": m.get("context_length"),
        "in_per_m": openrouter.per_million(p.get("prompt")),
        "out_per_m": openrouter.per_million(p.get("completion")),
    }


def print_table(rows: list[dict], cols: list[tuple[str, str]]) -> None:
    def cell(r: dict, k: str) -> str:
        v = r.get(k)
        if isinstance(v, int) and not isinstance(v, bool):
            return f"{v:,}"
        return "" if v is None else str(v)

    widths = [max(len(h), *(len(cell(r, k)) for r in rows)) for k, h in cols]
    say("  ".join(h.ljust(w) for (_, h), w in zip(cols, widths, strict=True)).rstrip())
    for r in rows:
        say("  ".join(cell(r, k).ljust(w) for (k, _), w in zip(cols, widths, strict=True)).rstrip())


MODEL_COLS = [
    ("mark", ""),
    ("id", "ID"),
    ("name", "Name"),
    ("context", "Context"),
    ("in_per_m", "In $/M"),
    ("out_per_m", "Out $/M"),
]


# --- commands ----------------------------------------------------------------------------


def cmd_set_key(ctx: Ctx) -> int:
    a = ctx.args
    if a.from_file:
        src = Path(a.from_file)
        try:
            paths.check_private(src)
            raw = src.read_text(encoding="utf-8")
        except paths.PermissionProblem as e:
            raise Refused(f"{e}; the source file must be 0600") from None
        except OSError as e:
            raise ValidationError(f"cannot read {src}: {e.strerror}") from None
    else:
        raw = read_secret("OpenRouter key for Open WebUI (hidden): ", False)
    secrets.register(raw.strip())
    try:
        key = secrets.clean_key(raw)
    except secrets.KeyFormatError as e:
        raise ValidationError(str(e)) from None
    ctx.key_prefix = key[:9]

    existing = None
    if ctx.key_path.exists():
        try:
            existing = secrets.read_key(ctx.key_path)
            secrets.register(existing)
        except paths.PermissionProblem:
            existing = ""
    if existing is not None and existing != key and not a.force:
        shown = redact(existing) if existing else "an unreadable key"
        if not confirm(f"Replace the stored key ({shown}) with {redact(key)}?", a):
            raise Refused("a key is already stored; pass --force or confirm to replace it")

    info = check_key_live(ctx, key)
    if existing == key:
        say(f"That key is already stored at {ctx.key_path}: {redact(key)}")
        ctx.detail = "unchanged"
    else:
        secrets.write_key(ctx.key_path, key)
        say(f"Stored {redact(key)} at {ctx.key_path} (0600)")
        ctx.detail = "stored"
    for field in openrouter.KEY_FIELDS:
        if field in info:
            say(f"  {field}: {info[field]}")
    if note := openrouter.expiry_warning(info.get("expires_at")):
        warn(f"warning: {note}")
    return OK


def cmd_models(ctx: Ctx) -> int:
    a = ctx.args
    models = fetch_models(ctx)
    by_id = {m["id"]: m for m in models}
    if a.search:
        try:
            allowed = set(allowlist.load(ctx.allowlist_path()))
        except (OSError, allowlist.AllowlistError):
            allowed = set()
        needle = a.search.lower()
        hits = [
            m for m in models if needle in m["id"].lower() or needle in str(m.get("name")).lower()
        ]
        rows = [{**model_row(m), "mark": "*" if m["id"] in allowed else ""} for m in hits]
        if a.json:
            say(json.dumps(rows, indent=2))
        elif rows:
            print_table(rows, MODEL_COLS)
            say(f"\n{len(rows)} of {len(models)} models match; * = on the allowlist")
        else:
            say(f"no model matches {a.search!r} ({len(models)} models)")
        return OK

    ids = load_allowlist(ctx)
    unknown = [i for i in ids if i not in by_id]
    rows = [{**model_row(by_id[i]), "mark": ""} for i in ids if i in by_id]
    rows += [{"id": i, "mark": "!", "name": "(unknown to OpenRouter)"} for i in unknown]
    if a.json:
        say(json.dumps({"models": rows, "unknown": unknown}, indent=2))
    else:
        print_table(rows, MODEL_COLS)
        if unknown:
            warn(f"\n{len(unknown)} unknown ID(s): {', '.join(unknown)} (try --search)")
    ctx.detail = f"{len(ids)} ids, {len(unknown)} unknown"
    return VALIDATION if unknown else OK


def cmd_apply(ctx: Ctx) -> int:
    a = ctx.args
    url = ctx.openrouter_url
    _ = ctx.webui_url  # refuse a remote Open WebUI before any network call
    ids = load_allowlist(ctx)
    key = load_key(ctx)
    check_key_live(ctx, key)
    known = {m["id"] for m in fetch_models(ctx)}
    unknown = [i for i in ids if i not in known]
    if unknown:
        raise ValidationError(
            f"unknown model ID(s) in the allowlist: {', '.join(unknown)} (check with `models`)"
        )

    ui = signin(ctx)
    try:
        openai = ui.get_connection_config()
        tasks = ui.get_task_config()
        local_ids = {m["id"] for m in ui.list_models() if webui.is_local_model(m) and "id" in m}
    except (net.HttpError, net.Unreachable) as e:
        raise Failed(f"reading the Open WebUI config failed: {e}") from None
    p = plan.plan_apply(
        openai,
        tasks,
        url=url,
        key=key,
        model_ids=ids,
        local_ids=local_ids,
        task_model=a.task_model,
    )
    for n in p.notes:
        say(n)
    lines = plan.diff(plan.view(openai, tasks), plan.view(p.openai_after, p.task_after))
    if not p.changes:
        say("already up to date; nothing written")
        ctx.detail = "no-op"
        return OK
    say("\nchanges:")
    for line in lines:
        say(f"  {line}")
    if a.dry_run:
        say("\ndry run: nothing written")
        ctx.detail = "dry-run"
        return OK

    snap = snapshot.save(
        ctx.state_dir,
        {
            "webui_url": ui.base_url,
            "url": url,
            "slot": p.slot,
            "mode": p.mode,
            "before": {"openai": openai, "tasks": tasks},
        },
    )
    say(f"\nsnapshot of the prior values: {snap}")
    written = False
    try:
        if p.openai_changes:
            ui.update_connection_config(p.openai_after)
            written = True
        if p.task_changes:
            ui.update_task_config(p.task_after)
            written = True
        got_o, got_t = ui.get_connection_config(), ui.get_task_config()
    except (net.HttpError, net.Unreachable) as e:
        if written:
            raise PartialFailure(
                f"apply failed after a partial change: {e}. Run `owh-openrouter remove` "
                f"to restore the prior values (snapshot {snap.name})"
            ) from None
        raise Failed(f"apply failed, nothing changed: {e}") from None
    if got_o != p.openai_after or got_t != p.task_after:
        raise PartialFailure(
            "Open WebUI does not show the values just written. Run `owh-openrouter status`, "
            f"then `owh-openrouter remove` to restore the prior values (snapshot {snap.name})"
        )
    say(f"applied: OpenRouter is connection {p.slot} with {len(ids)} models as {plan.PREFIX}.<id>")
    ctx.detail = f"{p.mode} slot={p.slot} models={len(ids)} snapshot={snap.name}"
    return OK


def cmd_status(ctx: Ctx) -> int:
    a = ctx.args
    report: dict = {"webui": {"url": a.webui_url}}
    ui = webui.WebUI(ctx.webui_url, a.timeout)
    try:
        report["webui"]["version"] = ui.version()
        report["webui"]["reachable"] = True
    except (net.HttpError, net.Unreachable) as e:
        report["webui"].update(reachable=False, error=str(e))

    stored = None
    kf: dict = {"path": str(ctx.key_path), "present": ctx.key_path.exists()}
    if kf["present"]:
        try:
            stored = load_key(ctx)
            kf["key"] = redact(stored)
        except OwhError as e:
            kf["error"] = str(e)
    report["key_file"] = kf

    if report["webui"]["reachable"] and not a.no_login:
        ui = signin(ctx)
        try:
            openai = ui.get_connection_config()
            tasks = ui.get_task_config()
            models = ui.list_models()
        except (net.HttpError, net.Unreachable) as e:
            raise Failed(f"reading the Open WebUI config failed: {e}") from None
        conns = []
        for i, u in enumerate(openai["OPENAI_API_BASE_URLS"]):
            c = openai["OPENAI_API_CONFIGS"].get(str(i)) or {}
            k = openai["OPENAI_API_KEYS"][i]
            conns.append(
                {
                    "index": i,
                    "url": u,
                    "enabled": bool(openai["ENABLE_OPENAI_API"]) and c.get("enable", True),
                    "prefix_id": c.get("prefix_id"),
                    "model_ids": len(c.get("model_ids") or []),
                    "key": redact(k) if k else None,
                    "matches_key_file": bool(stored) and k == stored,
                }
            )
        local = {m.get("id") for m in models if webui.is_local_model(m)}
        n_or = sum(str(m.get("id", "")).startswith(f"{plan.PREFIX}.") for m in models)
        ext = tasks.get("TASK_MODEL_EXTERNAL")
        report.update(
            openai_enabled=openai["ENABLE_OPENAI_API"],
            connections=conns,
            task_model={
                "TASK_MODEL": tasks.get("TASK_MODEL"),
                "TASK_MODEL_EXTERNAL": ext,
                "external_is_local": bool(ext) and ext in local,
            },
            models_listed={
                "openrouter": n_or,
                "local": len(local),
                "total": len(models),
            },
        )
    if stored:
        try:
            info = check_key_live(ctx, stored)
            report["openrouter_key"] = {k: info[k] for k in openrouter.KEY_FIELDS if k in info}
            if note := openrouter.expiry_warning(info.get("expires_at")):
                report["openrouter_key"]["warning"] = note
        except OwhError as e:
            report["openrouter_key"] = {"error": str(e)}
    snaps = snapshot.all_paths(ctx.state_dir, ui.base_url)
    report["snapshots"] = {"count": len(snaps), "earliest": str(snaps[0]) if snaps else None}

    if a.json:
        say(json.dumps(report, indent=2))
    else:
        w = report["webui"]
        if w["reachable"]:
            say(f"Open WebUI {w['version']} at {w['url']}")
        else:
            say(f"Open WebUI unreachable at {w['url']}: {w['error']}")
        say(f"key file: {kf.get('key') or kf.get('error') or 'none'} ({kf['path']})")
        for c in report.get("connections", []):
            on = "on " if c["enabled"] else "off"
            match = " = key file" if c["matches_key_file"] else ""
            pre = f" prefix {c['prefix_id']}" if c["prefix_id"] else ""
            say(
                f"connection {c['index']} [{on}] {c['url']}{pre}, {c['model_ids']} allowlisted, "
                f"key {c['key'] or 'none'}{match}"
            )
        if "task_model" in report:
            t = report["task_model"]
            local = "local" if t["external_is_local"] else "NOT a local model"
            say(f"task model for cloud chats: {t['TASK_MODEL_EXTERNAL']!r} ({local})")
            n = report["models_listed"]
            say(f"model list: {n['openrouter']} OpenRouter, {n['local']} local, {n['total']} total")
        if "openrouter_key" in report:
            k = dict(report["openrouter_key"])
            note = k.pop("warning", None)
            say("OpenRouter key: " + ", ".join(f"{f} {v}" for f, v in k.items()))
            if note:
                warn(f"warning: {note}")
        s = report["snapshots"]
        say(f"snapshots: {s['count']}" + (f", earliest {s['earliest']}" if s["earliest"] else ""))
    ctx.detail = "reachable" if report["webui"]["reachable"] else "unreachable"
    return OK if report["webui"]["reachable"] else Failed.code


def cmd_remove(ctx: Ctx) -> int:
    a = ctx.args
    target = ctx.webui_url
    path = Path(a.snapshot) if a.snapshot else snapshot.earliest(ctx.state_dir, target)
    if path is None:
        where = snapshot.directory(ctx.state_dir)
        raise Refused(f"no OWH snapshot of {target} in {where}; nothing to restore")
    try:
        snap = snapshot.load(path)
    except paths.PermissionProblem as e:
        raise Refused(str(e)) from None
    except (OSError, ValueError) as e:
        raise ValidationError(f"cannot use snapshot {path}: {e}") from None
    if str(snap.get("webui_url", "")).rstrip("/") != target:
        raise Refused(f"snapshot {path.name} was taken of {snap.get('webui_url')}, not {target}")
    say(f"restoring from snapshot {path}")
    ui = signin(ctx)
    try:
        openai = ui.get_connection_config()
        tasks = ui.get_task_config()
    except (net.HttpError, net.Unreachable) as e:
        raise Failed(f"reading the Open WebUI config failed: {e}") from None
    o_after, t_after, notes = plan.plan_remove(openai, tasks, snap)
    for n in notes:
        say(n)
    lines = plan.diff(plan.view(openai, tasks), plan.view(o_after, t_after))
    written = False
    if lines or o_after != openai or t_after != tasks:
        say("\nchanges:")
        for line in lines:
            say(f"  {line}")
        try:
            if o_after != openai:
                ui.update_connection_config(o_after)
                written = True
            if t_after != tasks:
                ui.update_task_config(t_after)
                written = True
            got_o, got_t = ui.get_connection_config(), ui.get_task_config()
        except (net.HttpError, net.Unreachable) as e:
            if written:
                raise PartialFailure(f"remove failed half-way: {e}. Run it again.") from None
            raise Failed(f"remove failed, nothing changed: {e}") from None
        if got_o != o_after or got_t != t_after:
            raise PartialFailure("Open WebUI does not show the restored values; run remove again")
        say(f"restored; the snapshot is kept at {path}")
        ctx.detail = f"restored from {path.name}"
    else:
        say("nothing to restore; Open WebUI already has the snapshot's values")
        ctx.detail = "no-op"

    if a.delete_key and ctx.key_path.exists():
        if confirm(f"Delete the stored key file {ctx.key_path}?", a):
            ctx.key_path.unlink()
            say(f"deleted {ctx.key_path} (revoke the key on openrouter.ai as well)")
            ctx.detail += " key-deleted"
        else:
            say("key file kept")
    return OK


COMMANDS = {
    "set-key": cmd_set_key,
    "models": cmd_models,
    "apply": cmd_apply,
    "status": cmd_status,
    "remove": cmd_remove,
}


# --- parser and main ---------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="owh-openrouter",
        description="Add an OpenRouter connection to a local Open WebUI.",
        epilog="exit codes: 0 ok, 1 validation, 2 usage, 3 refused, 4 failed (nothing changed), "
        "5 failed after a partial change (run `remove`)",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("--webui-url", default=webui.DEFAULT_URL)
    p.add_argument("--openrouter-url", default=openrouter.DEFAULT_URL)
    p.add_argument("--state-dir", default=None, help="default: ~/.local/state/owh")
    p.add_argument("--config-dir", default=None, help="default: ~/.config/owh")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument(
        "--allow-remote", action="store_true", help="allow an Open WebUI URL off this machine"
    )
    p.add_argument("--timeout", type=float, default=net.DEFAULT_TIMEOUT, help="seconds")

    login = argparse.ArgumentParser(add_help=False)
    login.add_argument("--email", help="Open WebUI admin e-mail (asked if omitted)")
    login.add_argument(
        "--password-stdin", action="store_true", help="read the admin password from stdin"
    )
    js = argparse.ArgumentParser(add_help=False)
    js.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    al = argparse.ArgumentParser(add_help=False)
    al.add_argument("--allowlist", help=f"default: {REPO_ALLOWLIST}")

    sub = p.add_subparsers(dest="command", required=True)
    sk = sub.add_parser("set-key", help="store the dedicated OpenRouter key")
    sk.add_argument("--from-file", help="read the key from a 0600 file instead of a prompt")
    sk.add_argument("--force", action="store_true", help="replace a stored key without asking")
    m = sub.add_parser("models", parents=[al, js], help="check the allowlist, or search models")
    m.add_argument("--search", metavar="TEXT", help="search all OpenRouter models")
    ap = sub.add_parser("apply", parents=[login, al], help="write the connection into Open WebUI")
    ap.add_argument("--dry-run", action="store_true", help="show the changes, write nothing")
    ap.add_argument("--task-model", help="local model for titles/tags of cloud chats")
    st = sub.add_parser("status", parents=[login, js], help="show what is configured")
    st.add_argument("--no-login", action="store_true", help="skip what needs the admin password")
    rm = sub.add_parser("remove", parents=[login], help="restore the pre-apply configuration")
    rm.add_argument("--snapshot", metavar="FILE", help="default: the earliest OWH snapshot")
    rm.add_argument("--delete-key", action="store_true", help="also delete the stored key file")
    rm.add_argument("--yes", action="store_true", help="do not ask before deleting the key")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    ctx = Ctx(args)
    try:
        code = COMMANDS[args.command](ctx)
    except OwhError as e:
        warn(f"owh-openrouter: {e}")
        code = e.code
    except (net.HttpError, net.Unreachable) as e:
        warn(f"owh-openrouter: {e}")
        code = Failed.code
    except KeyboardInterrupt:
        warn("owh-openrouter: interrupted")
        code = Failed.code
    log_action(ctx, args.command, "ok" if code == OK else f"exit={code}")
    return code


if __name__ == "__main__":
    sys.exit(main())
