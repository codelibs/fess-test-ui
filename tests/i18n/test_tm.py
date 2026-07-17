"""Integration tests for the i18n singleton: init() + tm()."""
from pathlib import Path

import pytest

from fess.test import i18n

FIXTURES = str(Path(__file__).parent / "fixtures")


def setup_function(_):
    """Reset singleton state before each test."""
    i18n._reset_for_tests()


def test_init_then_tm_returns_localized():
    i18n.init("ja", FIXTURES)
    assert i18n.tm("errors.result_size_exceeded") == "これ以上の結果は表示できません。"


def test_tm_falls_back_to_base():
    i18n.init("ja", FIXTURES)
    assert i18n.tm("errors.invalid_query_parse_error") == "The given query is invalid."


def test_tm_substitutes_positional_hole():
    i18n.init("ja", FIXTURES)
    assert i18n.tm("errors.invalid_query_unsupported_sort_field",
                   "nosuchfield") == "指定されたソート nosuchfield はサポートされていません。"


def test_tm_substitutes_multiple_holes():
    i18n.init("ja", FIXTURES)  # falls back to base for this key
    assert i18n.tm("errors.two_holes", "a", "b") == "Sort a is unsupported on field b."


def test_tm_leaves_hole_untouched_when_no_arg_given():
    i18n.init("ja", FIXTURES)
    assert "{0}" in i18n.tm("errors.invalid_query_unsupported_sort_field")


def test_tm_uses_default_when_missing():
    i18n.init("ja", FIXTURES)
    assert i18n.tm("errors.nope", default="X") == "X"


def test_tm_raises_when_missing_and_no_default():
    i18n.init("ja", FIXTURES)
    with pytest.raises(KeyError):
        i18n.tm("errors.nope")


def test_tm_raises_when_not_initialized():
    with pytest.raises(RuntimeError, match="not initialized"):
        i18n.tm("errors.result_size_exceeded")


def test_tm_and_t_are_separate_catalogs():
    """A label key must not resolve through tm(), nor a message key through t()."""
    i18n.init("ja", FIXTURES)
    with pytest.raises(KeyError):
        i18n.tm("labels.login")
    with pytest.raises(KeyError):
        i18n.t("errors.result_size_exceeded")


def test_message_sizes_reported():
    i18n.init("ja", FIXTURES)
    sizes = i18n.message_sizes()
    assert sizes["base"] >= 4
    assert sizes["lang"] >= 2
