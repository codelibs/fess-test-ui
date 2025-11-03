from fess.test.ui import FessContext

from . import add, delete


def run(context: FessContext) -> None:
    add.run(context)
    # Note: role does not have update functionality in Fess UI
    delete.run(context)
