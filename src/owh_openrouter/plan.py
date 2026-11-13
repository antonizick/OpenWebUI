"""Pure functions: the state `apply` and `remove` want, and a redacted diff of it.

Placement (spec R1): reuse a slot that already points at the OpenRouter URL ("update"); else
replace the dead default `https://api.openai.com/v1` entry that has no key ("replace"); else
append ("append"). A connection with a key or a non-default URL is never overwritten.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass

from .secrets import redact

PREFIX = "OR"  # Open WebUI adds the dot: OR.<id> (findings §2.3)
DEAD_URL = "https://api.openai.com/v1"
TASK_MODEL_CANDIDATES = ("qwen3:4b-instruct", "qwen3:8b")  # ADR-0005
OWH_CONN_FIELDS = {"enable": True, "prefix_id": PREFIX, "connection_type": "external"}


@dataclass
class ApplyPlan:
    openai_before: dict
    openai_after: dict
    task_before: dict
    task_after: dict
    slot: int
    mode: str  # update | replace | append
    notes: list[str]

    @property
    def openai_changes(self) -> bool:
        return self.openai_before != self.openai_after

    @property
    def task_changes(self) -> bool:
        return self.task_before != self.task_after

    @property
    def changes(self) -> bool:
        return self.openai_changes or self.task_changes


def find_url(openai: dict, url: str) -> int | None:
    for i, u in enumerate(openai["OPENAI_API_BASE_URLS"]):
        if u.rstrip("/") == url.rstrip("/"):
            return i
    return None


def place(openai: dict, url: str) -> tuple[int, str]:
    i = find_url(openai, url)
    if i is not None:
        return i, "update"
    for i, u in enumerate(openai["OPENAI_API_BASE_URLS"]):
        if u.rstrip("/") == DEAD_URL and not openai["OPENAI_API_KEYS"][i]:
            return i, "replace"
    return len(openai["OPENAI_API_BASE_URLS"]), "append"


def choose_task_model(
    current: str | None, local_ids: set[str], wanted: str | None
) -> tuple[str | None, str]:
    """The external task model to set (None = leave it) and a note saying why."""
    if wanted:
        if wanted in local_ids:
            return wanted, f"task model for cloud chats: {wanted} (as asked)"
        return None, f"warning: {wanted} is not a local model in Open WebUI; task model unchanged"
    if current and current in local_ids:
        return current, f"task model for cloud chats: {current} (already local, kept)"
    for c in TASK_MODEL_CANDIDATES:
        if c in local_ids:
            return c, f"task model for cloud chats: {c} (titles, tags, follow-ups stay local)"
    return None, (
        "warning: neither qwen3:4b-instruct nor qwen3:8b is installed in Ollama; task model "
        "unchanged, so titles and tags of cloud chats will also go to OpenRouter"
    )


def plan_apply(
    openai: dict,
    tasks: dict,
    *,
    url: str,
    key: str,
    model_ids: list[str],
    local_ids: set[str],
    task_model: str | None = None,
) -> ApplyPlan:
    if not model_ids:
        raise ValueError("empty allowlist")
    after = copy.deepcopy(openai)
    slot, mode = place(openai, url)
    notes: list[str] = []
    urls, keys, configs = (
        after["OPENAI_API_BASE_URLS"],
        after["OPENAI_API_KEYS"],
        after["OPENAI_API_CONFIGS"],
    )
    old_conf = configs.get(str(slot), {}) if mode == "update" else {}
    new_conf = {**old_conf, **OWH_CONN_FIELDS, "model_ids": list(model_ids)}
    if mode == "append":
        urls.append(url)
        keys.append(key)
        notes.append(
            f"connection {slot}: appended (no empty {DEAD_URL} slot to reuse; "
            "existing connections are kept)"
        )
    else:
        urls[slot] = url
        keys[slot] = key
        if mode == "replace":
            notes.append(f"connection {slot}: replaces the unused {DEAD_URL} entry (R1)")
    configs[str(slot)] = new_conf
    if after["ENABLE_OPENAI_API"] is not True:
        notes.append("OpenAI-compatible connections were disabled; enabling them")
        after["ENABLE_OPENAI_API"] = True

    task_after = dict(tasks)
    chosen, note = choose_task_model(tasks.get("TASK_MODEL_EXTERNAL"), local_ids, task_model)
    notes.append(note)
    if chosen is not None:
        task_after["TASK_MODEL_EXTERNAL"] = chosen
    return ApplyPlan(openai, after, tasks, task_after, slot, mode, notes)


def plan_remove(openai: dict, tasks: dict, snap: dict) -> tuple[dict, dict, list[str]]:
    """Put back what the snapshot had in OWH's slot, and the prior task model.

    Other connections (added after the snapshot) are left alone.
    """
    before_o = snap["before"]["openai"]
    before_t = snap["before"]["tasks"]
    after = copy.deepcopy(openai)
    notes: list[str] = []
    j = find_url(openai, snap["url"])
    slot = snap["slot"]
    urls, keys, configs = (
        after["OPENAI_API_BASE_URLS"],
        after["OPENAI_API_KEYS"],
        after["OPENAI_API_CONFIGS"],
    )
    if j is None:
        notes.append("the OpenRouter connection is already gone")
    elif snap["mode"] == "append" or slot >= len(before_o["OPENAI_API_BASE_URLS"]):
        del urls[j], keys[j]
        after["OPENAI_API_CONFIGS"] = {
            str(int(k) - 1 if int(k) > j else int(k)): v for k, v in configs.items() if int(k) != j
        }
        notes.append(f"connection {j}: removed")
    else:
        urls[j] = before_o["OPENAI_API_BASE_URLS"][slot]
        keys[j] = before_o["OPENAI_API_KEYS"][slot]
        prior = before_o["OPENAI_API_CONFIGS"].get(str(slot))
        if prior is None:
            configs.pop(str(j), None)
        else:
            configs[str(j)] = copy.deepcopy(prior)
        notes.append(f"connection {j}: restored to {urls[j]}")
    after["ENABLE_OPENAI_API"] = before_o["ENABLE_OPENAI_API"]
    task_after = dict(tasks)
    task_after["TASK_MODEL_EXTERNAL"] = before_t.get("TASK_MODEL_EXTERNAL")
    return after, task_after, notes


def view(openai: dict, tasks: dict) -> dict[str, object]:
    """Flatten to path -> value with every key redacted, for diffs and status."""
    out: dict[str, object] = {"ENABLE_OPENAI_API": openai.get("ENABLE_OPENAI_API")}
    for i, u in enumerate(openai["OPENAI_API_BASE_URLS"]):
        k = openai["OPENAI_API_KEYS"][i]
        out[f"connection[{i}].url"] = u
        out[f"connection[{i}].key"] = redact(k) if k else "(none)"
        for f, v in sorted((openai["OPENAI_API_CONFIGS"].get(str(i)) or {}).items()):
            out[f"connection[{i}].{f}"] = redact(v) if f == "key" and v else v
    out["TASK_MODEL_EXTERNAL"] = tasks.get("TASK_MODEL_EXTERNAL")
    return out


def diff(before: dict[str, object], after: dict[str, object]) -> list[str]:
    lines = []
    for k in list(before) + [k for k in after if k not in before]:
        if k not in after:
            lines.append(f"- {k}: {_fmt(before[k])}")
        elif k not in before:
            lines.append(f"+ {k}: {_fmt(after[k])}")
        elif before[k] != after[k]:
            lines.append(f"~ {k}: {_fmt(before[k])} -> {_fmt(after[k])}")
    return lines


def _fmt(v: object) -> str:
    if isinstance(v, list) and len(v) > 3:
        return f"[{len(v)} items: {', '.join(map(str, v))}]"
    return repr(v) if isinstance(v, str) else str(v)
