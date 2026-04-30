"""Unit tests for fess.test.i18n.labels."""
from pathlib import Path

import pytest

from fess.test.i18n.labels import LabelStrings

FIXTURES = Path(__file__).parent / "fixtures"


def test_loads_japanese_label():
    ls = LabelStrings("ja", str(FIXTURES))
    assert ls.get("labels.login") == "ログイン"


def test_loads_brazilian_portuguese_label():
    ls = LabelStrings("pt_BR", str(FIXTURES))
    assert ls.get("labels.login") == "Entrar"


def test_falls_back_to_base_when_key_missing_in_lang():
    # labels.menu_bad_word is in fess_label.properties but NOT fess_label_ja.properties
    ls = LabelStrings("ja", str(FIXTURES))
    assert ls.get("labels.menu_bad_word") == "Bad Words"


def test_falls_back_to_default_when_key_missing_everywhere():
    ls = LabelStrings("ja", str(FIXTURES))
    assert ls.get("labels.does_not_exist", default="X") == "X"


def test_raises_keyerror_when_key_missing_and_no_default():
    ls = LabelStrings("ja", str(FIXTURES))
    with pytest.raises(KeyError):
        ls.get("labels.does_not_exist")


def test_handles_unicode_escape_in_value():
    ls = LabelStrings("ja", str(FIXTURES))  # falls back to base for this key
    assert ls.get("labels.unicode_test") == "café"


def test_skips_comment_lines():
    ls = LabelStrings("ja", str(FIXTURES))
    # Should not crash; comments don't introduce bogus keys
    with pytest.raises(KeyError):
        ls.get("# Sample English labels for testing")


def test_handles_line_continuation():
    ls = LabelStrings("ja", str(FIXTURES))
    # Java .properties: "line one \\\n  continued" → "line one continued"
    val = ls.get("labels.continuation_test")
    assert val == "line one continued"


def test_raises_filenotfound_when_lang_file_missing():
    with pytest.raises(FileNotFoundError):
        LabelStrings("xx", str(FIXTURES))


def test_raises_filenotfound_when_base_file_missing(tmp_path):
    # No fess_label.properties in tmp_path
    with pytest.raises(FileNotFoundError):
        LabelStrings("ja", str(tmp_path))


def test_lang_file_overrides_base():
    ls = LabelStrings("ja", str(FIXTURES))
    # labels.login is in both; lang-specific should win
    assert ls.get("labels.login") == "ログイン"


def test_size_reports_loaded_key_counts():
    ls = LabelStrings("ja", str(FIXTURES))
    sizes = ls.sizes()  # returns dict {'lang': int, 'base': int}
    assert sizes["base"] >= 6  # 6+ keys in fixture
    assert sizes["lang"] >= 4
