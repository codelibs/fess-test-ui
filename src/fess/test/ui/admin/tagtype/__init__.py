import logging

from fess.test.ui import FessContext
from fess.test.ui.version import fess_version

from . import add, delete, search, update, validation

logger = logging.getLogger(__name__)

# The first Fess with the Tag admin screen (codelibs/fess#3551).
TAG_TYPE_SINCE = (15, 9)


def run(context: FessContext) -> None:
    version = fess_version(context)
    if version < TAG_TYPE_SINCE:
        logger.info(f"Fess {version[0]}.{version[1]} has no /admin/tagtype/: "
                    f"skipping the tagtype module")
        return
    # Order matters: every leaf works on the tag add creates. validation runs
    # before update because its duplicate check re-creates add's exact
    # name + owner pair, which update then moves to another owner.
    add.run(context)
    search.run(context)
    validation.run(context)
    update.run(context)
    delete.run(context)
