from fess.test.ui import FessContext

from . import add, delete, validation


def run(context: FessContext) -> None:
    add.run(context)
    # Note: role does not have update functionality in Fess UI
    validation.run(context)
    delete.run(context)
