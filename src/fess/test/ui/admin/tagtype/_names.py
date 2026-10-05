"""Test data shared by the tagtype leaves, derived from the run's label name
so that every leaf (and a rerun of one leaf via TEST_MODULES) agrees on it."""

from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext

LIST_PATH = "/admin/tagtype/"
DETAILS_PATH = "/admin/tagtype/details/4/"


def tag_name(context: FessContext) -> str:
    return f"tag{context.create_label_name()}"


def owner(context: FessContext) -> str:
    """The owner add.py creates the tag with."""
    return f"own{context.create_label_name().lower()}"


def new_owner(context: FessContext) -> str:
    """The owner update.py moves the tag to."""
    return f"new{context.create_label_name().lower()}"


def open_list(context: FessContext, page) -> None:
    """Reach the tag list through the sidebar, as an admin would."""
    page.click(f"text={t(Labels.MENU_CRAWL)}")
    page.click(f"text={t(Labels.MENU_TAG_TYPE)}")
    page.wait_for_load_state("domcontentloaded")
