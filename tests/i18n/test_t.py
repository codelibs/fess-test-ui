"""Integration tests for the i18n singleton: init() + t()."""
from pathlib import Path

import pytest

from fess.test import i18n

FIXTURES = str(Path(__file__).parent / "fixtures")


def setup_function(_):
    """Reset singleton state before each test."""
    i18n._reset_for_tests()


def test_init_then_t_returns_localized():
    i18n.init("ja", FIXTURES)
    assert i18n.t("labels.login") == "ログイン"
    assert i18n.selected_lang() == "ja"


def test_t_falls_back_to_base():
    i18n.init("ja", FIXTURES)
    assert i18n.t("labels.menu_bad_word") == "Bad Words"  # base fallback


def test_t_uses_default_when_missing():
    i18n.init("ja", FIXTURES)
    assert i18n.t("labels.nope", default="X") == "X"


def test_t_raises_when_missing_and_no_default():
    i18n.init("ja", FIXTURES)
    with pytest.raises(KeyError):
        i18n.t("labels.nope")


def test_t_raises_when_not_initialized():
    with pytest.raises(RuntimeError, match="not initialized"):
        i18n.t("labels.login")


def test_init_idempotent_with_same_args():
    i18n.init("ja", FIXTURES)
    i18n.init("ja", FIXTURES)  # should not error
    assert i18n.selected_lang() == "ja"


def test_selected_browser_locale():
    i18n.init("pt_BR", FIXTURES)
    assert i18n.selected_browser_locale() == "pt-BR"


def test_init_with_pt_br():
    i18n.init("pt_BR", FIXTURES)
    assert i18n.t("labels.login") == "Entrar"
