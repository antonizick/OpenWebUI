from pathlib import Path

import pytest

from owh_openrouter import allowlist


def test_parses_ids_comments_and_blanks():
    text = "# header\n\nvendor/a\n  vendor/b:free  # trailing\n"
    assert allowlist.parse(text) == ["vendor/a", "vendor/b:free"]


def test_duplicates_rejected():
    with pytest.raises(allowlist.AllowlistError, match="duplicate"):
        allowlist.parse("vendor/a\nvendor/a\n")


@pytest.mark.parametrize("bad", ["no-slash", "a b/c", "vendor/", "/model", "v/m;rm", "v/m\x00"])
def test_invalid_characters_rejected(bad):
    with pytest.raises(allowlist.AllowlistError, match="invalid"):
        allowlist.parse(bad + "\n")


def test_shipped_file_is_the_confirmed_allowlist():
    # ADR-0014: the eight models Nick confirmed for owner question 1.
    path = Path(__file__).parent.parent / "config" / "openrouter-models.txt"
    assert allowlist.load(path) == [
        "anthropic/claude-sonnet-5.5",
        "anthropic/claude-haiku-5.5",
        "google/gemini-4-hydrogen",
        "openai/gpt-6.1-terra",
        "google/gemma-4-31b-it:free",
        "deepseek/deepseek-v4.1-flash-1017",
        "xiaomi/mimo-v2.6-pro",
        "z-ai/glm-5.3-flash",
    ]
