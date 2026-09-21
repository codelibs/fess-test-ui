"""Strings from the bootstrap static theme's own i18n bundle.

Since fess#3460 the search pages (/, /search, /help, /profile, /cache,
/advance, /error/*) are the built-in bootstrap static-theme SPA, not JSPs.
The SPA does not render fess_label/fess_message text: it localizes itself
from its own JSON bundle, served at
/themes/bootstrap/i18n/messages.<locale>.json, where <locale> is the Fess
locale with a hyphen (pt_BR -> pt-BR). Assertions on SPA-rendered text
therefore read that bundle, the same way labels are read through t().

Messages the server puts into an API response (e.g. /api/v2/search errors)
are still fess_message text; use tm() for those.
"""
from typing import Dict

from fess.test.i18n import selected_lang
from fess.test.ui import FessContext

BUNDLE_PATH = "/themes/bootstrap/i18n/messages.{locale}.json"

_bundles: Dict[str, dict] = {}


class ThemeKeys:
    """Theme bundle keys the suite depends on (the keys.py counterpart)."""
    SEARCH_DID_NOT_MATCH = "search.did_not_match"
    RESULT_CACHE = "result.cache"
    CACHE_NOT_FOUND = "labels.cache_not_found"
    PROFILE_ERROR_MISMATCH = "profile.error_mismatch"
    ADVANCE_TITLE = "advance.title"
    ERROR_TITLE_400 = "error.title_400"
    ERROR_TITLE_404 = "error.title_404"
    ERROR_TITLE_429 = "error.title_429"
    ERROR_TITLE_500 = "error.title_500"
    ERROR_DETAIL_DOCID_NOT_FOUND = "error.detail_docid_not_found"
    ERROR_DETAIL_BAD_AUTHENTICATION = "error.detail_bad_authentication"


def theme_locale() -> str:
    """The bundle locale for the run's TEST_LANG (pt_BR -> pt-BR)."""
    return selected_lang().replace("_", "-")


def tt(context: FessContext, key: str, *args: str) -> str:
    """Theme-bundle text for `key`, with {0}, {1}, ... replaced by args.

    Raises KeyError when the bundle has no such key: the SPA would render
    the raw key there, so a missing key is a failure, not a fallback.
    """
    locale = theme_locale()
    if locale not in _bundles:
        _bundles[locale] = context.api_get(BUNDLE_PATH.format(locale=locale))
    text = _bundles[locale][key]
    for index, value in enumerate(args):
        text = text.replace("{" + str(index) + "}", value)
    return text
