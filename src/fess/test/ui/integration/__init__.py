from fess.test.ui import FessContext
from playwright.sync_api import Playwright, sync_playwright

from . import crawler_workflow, user_permission_workflow, dictionary_workflow, suggest_workflow


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def run(context: FessContext) -> None:
    """Run all integration tests"""
    crawler_workflow.run(context)
    user_permission_workflow.run(context)
    dictionary_workflow.run(context)
    suggest_workflow.run(context)


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
