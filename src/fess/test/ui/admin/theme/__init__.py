import logging

from fess.test.ui import FessContext
from fess.test.ui.version import STATIC_THEME_SINCE, fess_version

from . import lifecycle, rejection

logger = logging.getLogger(__name__)


def run(context: FessContext) -> None:
    version = fess_version(context)
    if version < STATIC_THEME_SINCE:
        logger.info(f"Fess {version[0]}.{version[1]} has no theme admin screen: "
                    f"skipping the theme module")
        return
    rejection.run(context)
    lifecycle.run(context)
