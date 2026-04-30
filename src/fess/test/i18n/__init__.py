"""Multi-language test support for fess-test-ui.

Public API:
    SUPPORTED_LANGS    -- list of Fess UI locales
    select_language    -- resolve TEST_LANG env value to a concrete locale
    to_browser_locale  -- convert Fess locale to BCP47 (later task)
    init               -- initialize singleton (later task)
    t                  -- label lookup (later task)
"""
import random as _random
from typing import Optional

# Matches fess_label_<x>.properties files in Fess
SUPPORTED_LANGS = [
    "de", "en", "es", "fr", "hi", "id", "it", "ja", "ko",
    "nl", "pl", "pt_BR", "ru", "tr", "zh_CN", "zh_TW",
]


def select_language(env_value: Optional[str] = None,
                    seed: Optional[int] = None) -> str:
    """Resolve TEST_LANG: explicit code | 'random'/None/'' -> random pick.

    Args:
        env_value: raw TEST_LANG value (e.g. 'ja', 'random', None, '')
        seed: optional seed for deterministic random selection

    Returns:
        Fess locale string (e.g. 'ja', 'pt_BR')

    Raises:
        ValueError: if env_value is not a supported locale and not 'random'/None/''
    """
    if env_value in (None, "", "random"):
        rng = _random.Random(seed) if seed is not None else _random
        return rng.choice(SUPPORTED_LANGS)
    if env_value not in SUPPORTED_LANGS:
        raise ValueError(
            f"unsupported TEST_LANG={env_value!r}; "
            f"must be one of {SUPPORTED_LANGS} or 'random'")
    return env_value
