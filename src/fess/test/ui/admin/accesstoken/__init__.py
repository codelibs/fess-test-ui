from fess.test.ui import FessContext

from . import add, delete, update, validation


def run(context: FessContext) -> None:
    add.run(context)
    update.run(context)
    validation.run(context)
    delete.run(context)
