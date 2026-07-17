from fess.test.ui import FessContext

from . import add, delete, update, job, validation


def run(context: FessContext) -> None:
    add.run(context)
    update.run(context)
    validation.run(context)
    job.run(context)
    delete.run(context)
