from fess.test.ui import FessContext

from . import add, update, delete


def run(context: FessContext) -> None:
    add.run(context)
    update.run(context)
    delete.run(context)
