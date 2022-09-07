from fess.test.ui import FessContext

from . import add, delete


def run(context: FessContext) -> None:
    add.run(context)
    delete.run(context)
