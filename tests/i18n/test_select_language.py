"""Unit tests for language selection logic."""
import pytest

from fess.test.i18n import select_language, SUPPORTED_LANGS


def test_returns_explicit_lang():
    assert select_language("ja") == "ja"
    assert select_language("pt_BR") == "pt_BR"


def test_random_when_value_is_random_keyword():
    # Seed makes the choice deterministic
    lang = select_language("random", seed=42)
    assert lang in SUPPORTED_LANGS


def test_random_when_value_is_none():
    lang = select_language(None, seed=42)
    assert lang in SUPPORTED_LANGS


def test_random_when_value_is_empty():
    lang = select_language("", seed=42)
    assert lang in SUPPORTED_LANGS


def test_seed_is_deterministic():
    a = select_language("random", seed=12345)
    b = select_language("random", seed=12345)
    assert a == b


def test_different_seeds_can_yield_different_results():
    # Try a handful of seeds; at least two should differ given 16 langs
    picks = {select_language("random", seed=s) for s in range(20)}
    assert len(picks) > 1


def test_raises_for_unsupported_lang():
    with pytest.raises(ValueError, match="unsupported"):
        select_language("xx")


def test_supported_langs_count():
    assert len(SUPPORTED_LANGS) == 16
    # Spot-check critical members
    for lang in ["ja", "en", "de", "pt_BR", "zh_CN", "zh_TW"]:
        assert lang in SUPPORTED_LANGS
