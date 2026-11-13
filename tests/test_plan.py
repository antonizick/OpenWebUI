import copy

import pytest

from owh_openrouter import plan
from tests.fakes.server import FAKE_KEY, TASK_CONFIG

URL = "https://openrouter.ai/api/v1"
IDS = ["vendor/a", "vendor/b"]
LOCAL = {"qwen3:4b-instruct", "qwen3:8b"}


def pristine():
    return {
        "ENABLE_OPENAI_API": True,
        "OPENAI_API_BASE_URLS": ["https://api.openai.com/v1"],
        "OPENAI_API_KEYS": [""],
        "OPENAI_API_CONFIGS": {},
    }


def tasks():
    return copy.deepcopy(TASK_CONFIG)


def mk(openai=None, t=None, **kw):
    args = {"url": URL, "key": FAKE_KEY, "model_ids": IDS, "local_ids": LOCAL, **kw}
    return plan.plan_apply(openai or pristine(), t or tasks(), **args)


def test_replaces_the_dead_default_entry():
    p = mk()
    assert (p.slot, p.mode) == (0, "replace")
    assert p.openai_after["OPENAI_API_BASE_URLS"] == [URL]
    assert p.openai_after["OPENAI_API_KEYS"] == [FAKE_KEY]
    assert p.openai_after["OPENAI_API_CONFIGS"] == {
        "0": {"enable": True, "prefix_id": "OR", "connection_type": "external", "model_ids": IDS}
    }
    assert p.task_after["TASK_MODEL_EXTERNAL"] == "qwen3:4b-instruct"
    assert {k: v for k, v in p.task_after.items() if k != "TASK_MODEL_EXTERNAL"} == {
        k: v for k, v in TASK_CONFIG.items() if k != "TASK_MODEL_EXTERNAL"
    }


def test_appends_when_the_openai_entry_has_a_key():
    o = pristine()
    o["OPENAI_API_KEYS"] = ["sk-real"]
    p = mk(o)
    assert (p.slot, p.mode) == (1, "append")
    assert p.openai_after["OPENAI_API_BASE_URLS"][0] == "https://api.openai.com/v1"
    assert p.openai_after["OPENAI_API_KEYS"][0] == "sk-real"
    assert any("appended" in n for n in p.notes)


def test_appends_next_to_a_non_default_url():
    o = pristine()
    o["OPENAI_API_BASE_URLS"] = ["http://127.0.0.1:9999/v1"]
    assert mk(o).mode == "append"


def test_second_plan_is_a_no_op_and_keeps_extra_fields():
    p1 = mk()
    o = copy.deepcopy(p1.openai_after)
    o["OPENAI_API_CONFIGS"]["0"]["tags"] = [{"name": "cloud"}]  # added by hand in the UI
    p2 = mk(o, p1.task_after)
    assert p2.mode == "update" and not p2.changes
    assert p2.openai_after["OPENAI_API_CONFIGS"]["0"]["tags"] == [{"name": "cloud"}]


def test_allowlist_change_updates_in_place():
    p1 = mk()
    p2 = mk(p1.openai_after, p1.task_after, model_ids=["vendor/c"])
    assert p2.mode == "update" and p2.openai_changes and not p2.task_changes
    assert p2.openai_after["OPENAI_API_CONFIGS"]["0"]["model_ids"] == ["vendor/c"]


def test_disabled_openai_is_enabled():
    o = pristine()
    o["ENABLE_OPENAI_API"] = None
    p = mk(o)
    assert p.openai_after["ENABLE_OPENAI_API"] is True
    assert any("enabling" in n for n in p.notes)


def test_empty_allowlist_refused():
    with pytest.raises(ValueError):
        mk(model_ids=[])


@pytest.mark.parametrize(
    ("current", "local", "wanted", "chosen"),
    [
        ("", LOCAL, None, "qwen3:4b-instruct"),
        ("", {"qwen3:8b"}, None, "qwen3:8b"),
        ("", set(), None, None),
        ("gemma2:9b", {"gemma2:9b", "qwen3:8b"}, None, "gemma2:9b"),  # an existing local choice
        ("OR.vendor/a", LOCAL, None, "qwen3:4b-instruct"),  # a cloud task model is replaced
        ("", LOCAL, "qwen3:8b", "qwen3:8b"),
        ("", LOCAL, "missing:1b", None),
    ],
)
def test_task_model_choice(current, local, wanted, chosen):
    got, note = plan.choose_task_model(current, local, wanted)
    assert got == chosen
    if chosen is None:
        assert note.startswith("warning")


def test_no_local_task_model_leaves_tasks_alone():
    p = mk(local_ids=set())
    assert not p.task_changes


def snap_of(p):
    return {
        "url": URL,
        "slot": p.slot,
        "mode": p.mode,
        "before": {"openai": p.openai_before, "tasks": p.task_before},
    }


def test_remove_after_replace_restores_exactly():
    p = mk()
    o, t, _ = plan.plan_remove(p.openai_after, p.task_after, snap_of(p))
    assert o == pristine() and t == tasks()


def test_remove_after_append_deletes_and_reindexes():
    before = pristine()
    before["OPENAI_API_KEYS"] = ["sk-real"]
    p = mk(before)
    cur = copy.deepcopy(p.openai_after)
    # Nick added a third connection after OWH.
    cur["OPENAI_API_BASE_URLS"].append("http://127.0.0.1:7/v1")
    cur["OPENAI_API_KEYS"].append("")
    cur["OPENAI_API_CONFIGS"]["2"] = {"prefix_id": "X"}
    o, _, notes = plan.plan_remove(cur, p.task_after, snap_of(p))
    assert o["OPENAI_API_BASE_URLS"] == ["https://api.openai.com/v1", "http://127.0.0.1:7/v1"]
    assert o["OPENAI_API_CONFIGS"] == {"1": {"prefix_id": "X"}}
    assert "removed" in notes[0]


def test_remove_restores_a_prior_config_entry():
    before = pristine()
    before["OPENAI_API_CONFIGS"] = {"0": {"enable": False}}
    p = mk(before)
    o, _, _ = plan.plan_remove(p.openai_after, p.task_after, snap_of(p))
    assert o == before


def test_remove_when_already_gone_only_restores_task_model():
    p = mk()
    o, t, notes = plan.plan_remove(pristine(), p.task_after, snap_of(p))
    assert o == pristine() and t == tasks()
    assert "already gone" in notes[0]


def test_remove_finds_a_moved_connection():
    p = mk()
    cur = copy.deepcopy(p.openai_after)
    cur["OPENAI_API_BASE_URLS"].insert(0, "http://127.0.0.1:7/v1")
    cur["OPENAI_API_KEYS"].insert(0, "")
    cur["OPENAI_API_CONFIGS"] = {"1": cur["OPENAI_API_CONFIGS"]["0"]}
    o, _, _ = plan.plan_remove(cur, p.task_after, snap_of(p))
    assert o["OPENAI_API_BASE_URLS"] == ["http://127.0.0.1:7/v1", "https://api.openai.com/v1"]
    assert o["OPENAI_API_CONFIGS"] == {}


def test_view_redacts_keys_and_diff_lists_changes():
    p = mk()
    a, b = plan.view(p.openai_before, p.task_before), plan.view(p.openai_after, p.task_after)
    text = "\n".join(plan.diff(a, b))
    assert FAKE_KEY not in text and FAKE_KEY[9:20] not in text
    assert (
        "~ connection[0].url: 'https://api.openai.com/v1' -> 'https://openrouter.ai/api/v1'" in text
    )
    assert "+ connection[0].prefix_id: 'OR'" in text
    assert "~ TASK_MODEL_EXTERNAL: '' -> 'qwen3:4b-instruct'" in text
    assert plan.diff(b, a)[-1].startswith("~ TASK_MODEL_EXTERNAL")
    assert any(line.startswith("- connection[0].prefix_id") for line in plan.diff(b, a))


def test_view_redacts_a_per_connection_key_field():
    o = pristine()
    o["OPENAI_API_CONFIGS"] = {"0": {"key": FAKE_KEY}}
    assert FAKE_KEY not in str(plan.view(o, {}))


def test_long_lists_are_summarised():
    assert plan._fmt(["a", "b", "c", "d"]).startswith("[4 items:")
