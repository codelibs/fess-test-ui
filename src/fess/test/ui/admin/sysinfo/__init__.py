"""Composes every /admin/ system-info test.

Like the general package, this one had no composer, so each leaf had to be
registered in main.py by hand. Registering the package instead means a new
module here is picked up by adding one line to this file.

Order preserves what main.py's default list used to do: the data-independent
structural pages first, then the ones that read crawl/search data.
"""
from fess.test.ui import FessContext

from . import (backup, configinfo, crawlinfo, failureurl, joblog, logfile,
               maintenance, searchlist, searchlog)


def run(context: FessContext) -> None:
    configinfo.run(context)
    logfile.run(context)
    crawlinfo.run(context)
    joblog.run(context)
    failureurl.run(context)
    searchlog.run(context)
    searchlist.run(context)
    backup.run(context)
    maintenance.run(context)
