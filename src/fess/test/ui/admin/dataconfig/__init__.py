from fess.test.ui import FessContext

from . import add, delete, update


def run(context: FessContext) -> None:
    add.run(context)
    update.run(context)
    delete.run(context)
