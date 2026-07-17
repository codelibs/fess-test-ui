from fess.test.ui import FessContext

from . import crawler_workflow, dictionary_workflow, suggest_workflow, user_permission_workflow


def run(context: FessContext) -> None:
    """Run all integration workflows.

    Composer only: main.py calls run(context) and owns the shared FessContext,
    so this file has no setup/destroy of its own. It also has no __main__
    block -- a package's __init__.py executes with __name__ set to the package
    name, never "__main__", so such a block could never fire. Run a single
    workflow directly instead: python -m fess.test.ui.integration.crawler_workflow
    """
    crawler_workflow.run(context)
    user_permission_workflow.run(context)
    dictionary_workflow.run(context)
    suggest_workflow.run(context)
