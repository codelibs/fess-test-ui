"""The Fess version under test, and the switch between the two search UIs.

Fess 15.9 (codelibs/fess#3460) serves the search pages -- /, /search, /help,
/profile, /cache, /advance, /error/* -- from the bundled bootstrap
theme SPA and renders errors in place; 15.8 and earlier serve JSPs
and redirect errors through error/redirect.jsp. A module asserting one of the
two UIs therefore keeps its JSP-era version next to it as <module>_jsp.py,
unchanged, and its run() starts with

    if run_jsp_variant(context, <module>_jsp):
        return

so both lines run real assertions. Delete the *_jsp.py modules, this switch
and the JSP-only keys in fess.test.i18n once no workflow targets Fess 15.8
or earlier (compose-fess15*.yaml).
"""
import logging
import re
from types import ModuleType
from typing import Optional, Tuple

import requests

from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

# The first Fess whose search pages are the theme SPA.
STATIC_THEME_SINCE = (15, 9)

# The first Fess whose JSP login page (/login/) no longer renders the
# "login page notification" (fess#3728): the theme shows it in the login
# modal from /api/v2/ui/config notifications.login instead.
LOGIN_NOTIFICATION_IN_THEME_SINCE = (15, 10)

# Every /api/admin/* response is an ApiResult, whose envelope carries the
# product version (major.minor, SystemHelper#getProductVersion) -- the 401
# an unauthenticated caller gets included, on 15.8 as on 15.9. The admin API
# takes an access token, not the suite's admin session, so the 401 is what
# the suite reads.
VERSION_PATH = "/api/admin/systeminfo"

_version: Optional[Tuple[int, int]] = None


def parse_version(text: str) -> Tuple[int, int]:
    """(major, minor) of a Fess version string such as '15.8' or '15.9.0'."""
    match = re.match(r"(\d+)\.(\d+)(?:\D|$)", text or "")
    if not match:
        raise ValueError(f"not a Fess version: {text!r}")
    return int(match.group(1)), int(match.group(2))


def fess_version(context: FessContext) -> Tuple[int, int]:
    """(major, minor) of the Fess under test, asked of the server once per run.

    Raises rather than guessing: running the wrong line's modules would
    report the UI as broken.
    """
    global _version
    if _version is None:
        url = context.url(VERSION_PATH)
        resp = requests.get(url, timeout=10)
        try:
            text = resp.json()["response"]["version"]
        except (ValueError, KeyError, TypeError) as e:
            raise RuntimeError(
                f"cannot tell the Fess version: {url} answered HTTP "
                f"{resp.status_code} without response.version") from e
        _version = parse_version(text)
        logger.info(f"Fess version under test: {text}")
    return _version


def run_jsp_variant(context: FessContext, jsp_module: ModuleType,
                    since: Tuple[int, int] = STATIC_THEME_SINCE) -> bool:
    """Run jsp_module on Fess older than `since` (default
    STATIC_THEME_SINCE); return whether it ran, i.e. whether the caller
    should stop there."""
    version = fess_version(context)
    if version >= since:
        return False
    logger.info(f"Fess {version[0]}.{version[1]} predates {since[0]}.{since[1]}: "
                f"running {jsp_module.__name__}")
    jsp_module.run(context)
    return True
