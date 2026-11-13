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


def test_shipped_file_parses_and_is_empty_for_now():
    path = Path(__file__).parent.parent / "config" / "openrouter-models.txt"
    assert allowlist.load(path) == []
