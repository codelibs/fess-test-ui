"""Composes every /admin/wizard/ test.

One leaf today. It is a package rather than a module so that a second
wizard test is picked up by adding a line here, not by remembering to edit
main.py -- the omission that left the six general modules unrun.
"""
from fess.test.ui import FessContext

from . import crawling_config


def run(context: FessContext) -> None:
    crawling_config.run(context)
