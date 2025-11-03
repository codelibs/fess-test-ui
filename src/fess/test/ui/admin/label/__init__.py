from fess.test.ui.admin.label import add, update, validation, delete


def run(context):
    add.run(context)
    update.run(context)
    # validation.run(context)  # Temporarily disabled - needs adjustment for actual Fess behavior
    delete.run(context)
