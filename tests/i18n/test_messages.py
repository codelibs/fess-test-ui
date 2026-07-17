"""Unit tests for fess.test.i18n.messages."""
from pathlib import Path

import pytest

from fess.test.i18n.messages import MessageStrings

FIXTURES = Path(__file__).parent / "fixtures"


def test_loads_japanese_message():
    ms = MessageStrings("ja", str(FIXTURES))
    assert ms.get("errors.result_size_exceeded") == "これ以上の結果は表示できません。"


def test_loads_brazilian_portuguese_message():
    ms = MessageStrings("pt_BR", str(FIXTURES))
    assert ms.get("errors.result_size_exceeded") == "Não é possível exibir mais resultados."


def test_falls_back_to_base_when_key_missing_in_lang():
    # Present in fess_message.properties but NOT fess_message_ja.properties
    ms = MessageStrings("ja", str(FIXTURES))
    assert ms.get("errors.invalid_query_parse_error") == "The given query is invalid."


def test_lang_file_overrides_base():
    ms = MessageStrings("ja", str(FIXTURES))
    assert ms.get("errors.result_size_exceeded") == "これ以上の結果は表示できません。"


def test_strips_leading_space_after_separator():
    # Fess writes "key = value"; Java .properties drops the leading space,
    # so an assertion comparing against rendered page text must not see it.
    ms = MessageStrings("ja", str(FIXTURES))
    assert ms.get("errors.invalid_query_parse_error").startswith("The given")


def test_falls_back_to_default_when_key_missing_everywhere():
    ms = MessageStrings("ja", str(FIXTURES))
    assert ms.get("errors.does_not_exist", default="X") == "X"


def test_raises_keyerror_when_key_missing_and_no_default():
    ms = MessageStrings("ja", str(FIXTURES))
    with pytest.raises(KeyError):
        ms.get("errors.does_not_exist")


def test_keyerror_names_the_message_family_not_labels():
    ms = MessageStrings("ja", str(FIXTURES))
    with pytest.raises(KeyError, match="fess_message"):
        ms.get("errors.does_not_exist")


def test_raises_filenotfound_when_lang_file_missing():
    with pytest.raises(FileNotFoundError):
        MessageStrings("xx", str(FIXTURES))


def test_raises_filenotfound_when_base_file_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        MessageStrings("ja", str(tmp_path))


def test_size_reports_loaded_key_counts():
    ms = MessageStrings("ja", str(FIXTURES))
    sizes = ms.sizes()
    assert sizes["base"] >= 4
    assert sizes["lang"] >= 2
