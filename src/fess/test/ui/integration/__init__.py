from fess.test.ui import FessContext

from . import crawler_workflow, user_permission_workflow, dictionary_workflow, suggest_workflow


def run(context: FessContext) -> None:
    """Run all integration tests"""
    crawler_workflow.run(context)
    user_permission_workflow.run(context)
    dictionary_workflow.run(context)
    suggest_workflow.run(context)
