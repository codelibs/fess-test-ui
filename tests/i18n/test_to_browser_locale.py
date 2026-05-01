"""Unit tests for to_browser_locale conversion."""
import pytest

from fess.test.i18n import to_browser_locale, SUPPORTED_LANGS


def test_japanese():
    assert to_browser_locale("ja") == "ja-JP"


def test_english():
    assert to_browser_locale("en") == "en-US"


def test_brazilian_portuguese():
    assert to_browser_locale("pt_BR") == "pt-BR"


def test_simplified_chinese():
    assert to_browser_locale("zh_CN") == "zh-CN"


def test_traditional_chinese():
    assert to_browser_locale("zh_TW") == "zh-TW"


def test_german():
    assert to_browser_locale("de") == "de-DE"


def test_korean():
    assert to_browser_locale("ko") == "ko-KR"


def test_turkish():
    assert to_browser_locale("tr") == "tr-TR"


def test_hindi():
    assert to_browser_locale("hi") == "hi-IN"


def test_indonesian():
    assert to_browser_locale("id") == "id-ID"


def test_every_supported_lang_has_a_mapping():
    """Every supported lang must convert to a BCP47 form (smoke check)."""
    for lang in SUPPORTED_LANGS:
        result = to_browser_locale(lang)
        assert "-" in result
        assert "_" not in result


def test_raises_for_unsupported():
    with pytest.raises(ValueError, match="unsupported"):
        to_browser_locale("xx")
