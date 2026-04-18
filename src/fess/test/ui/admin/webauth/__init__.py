"""webauth tests require an existing webConfig. We create a disposable one
('webauth-e2e') in add.py's run and delete it in delete.py's run so the
module is self-contained when invoked stand-alone."""
from fess.test.ui import FessContext

from ._const import WEBCONFIG_NAME
from . import add, delete, update


def run(context: FessContext) -> None:
    add.run(context)
    update.run(context)
    delete.run(context)
