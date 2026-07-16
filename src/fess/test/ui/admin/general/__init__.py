"""Composes every /admin/general/ test.

This package had no composer, so each leaf had to be registered in main.py by
hand — and six of them never were, which is why they went unrun long enough to
rot. Registering the package instead of its leaves means a new module here is
picked up by adding one line to this file.

Order: the read-only pages first, then the modules that mutate settings.
loginRequired goes last because a failure to restore it would send every later
module to the login screen.
"""
from fess.test.ui import FessContext

from . import (jsonResponse, logLevel, loginLink, loginRequired,
               notificationLogin, notificationSearchTop, pagedesign, plugin,
               popularWord, storage)


def run(context: FessContext) -> None:
    popularWord.run(context)
    pagedesign.run(context)
    storage.run(context)
    plugin.run(context)
    logLevel.run(context)
    jsonResponse.run(context)
    loginLink.run(context)
    notificationLogin.run(context)
    notificationSearchTop.run(context)
    loginRequired.run(context)
