"""Verify the admin console shell: its assets, the side menu and the search log date range.

Fess 15.10 replaced the admin console's Bootstrap/AdminLTE/jQuery stack with its own stylesheet and
script. What a page needs to show and run is the same on 15.9 and 15.10, so every check but the last
runs on both. The date range is two native date-time inputs on the new console and a date range picker
on the old one; the page says which it is (the new admin.js defines window.FessAdmin), so the suite
is green on a snapshot image that has not caught up with the new console yet, and each line asserts its own.

* every stylesheet, script, font and image the pages load answers, and no script reports an error
* a side menu group opens and closes, and the menu itself collapses and comes back
* on a phone-sized screen the side menu starts closed, opens over the page, and nothing scrolls sideways
* the date range of the search log survives a search, in the text field the server reads
* the long forms are split into tabs that open, and short fields stand side by side (new console only)
"""
import logging
import re
from typing import List

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_equal, assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

# A page of a list, one of a form and one with the date range.
PAGES = ["/admin/webconfig/", "/admin/general/", "/admin/searchlog/logs/"]
ASSET_PATH = re.compile(r"/(css|js|images)/")
RANGE_TEXT = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2} - \d{4}-\d{2}-\d{2} \d{2}:\d{2}$")

# favicon and the CSP directive Chromium does not know are not the console's
NOISE = ("favicon", "Unrecognized Content-Security-Policy directive")


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


SIDEBAR_WIDTH_ON_SCREEN = """() => {
    const r = document.querySelector('aside.main-sidebar').getBoundingClientRect();
    return Math.max(0, Math.min(r.right, window.innerWidth) - Math.max(r.left, 0));
}"""


def _sidebar_width(raw_page) -> float:
    """How much of the side menu is on screen; the 15.9 console left a narrow icon rail when collapsed."""
    return raw_page.evaluate(SIDEBAR_WIDTH_ON_SCREEN)


def _check_assets_and_scripts(raw_page, context: FessContext) -> None:
    problems: List[str] = []

    def on_response(response):
        if ASSET_PATH.search(response.url) and response.status >= 400:
            problems.append(f"HTTP {response.status} {response.url}")

    raw_page.on("response", on_response)
    raw_page.on("console", lambda msg: problems.append(f"console.error: {msg.text}")
                if msg.type == "error" and not any(n in msg.text for n in NOISE) else None)
    raw_page.on("pageerror", lambda exc: problems.append(f"pageerror: {exc}"))
    for path in PAGES:
        raw_page.goto(context.url(path))
        raw_page.wait_for_load_state("networkidle")
    raw_page.remove_listener("response", on_response)
    assert_true(not problems, f"admin pages loaded with problems: {problems}")


def _check_side_menu(raw_page, context: FessContext) -> None:
    raw_page.set_viewport_size({"width": 1280, "height": 800})
    raw_page.goto(context.url("/admin/webconfig/"))
    raw_page.wait_for_load_state("domcontentloaded")

    # a group that is not the current one; found by position, because a locator is looked up again at each
    # use and "not open" stops matching it once it opens
    index = raw_page.evaluate(
        "[...document.querySelectorAll('li.has-treeview')].findIndex(e => !e.classList.contains('menu-open'))")
    assert_true(index >= 0, "every menu group is open on load")
    group = raw_page.locator("li.has-treeview").nth(index)
    link = group.locator("> a.nav-link")
    sub = group.locator("> ul.nav-treeview")
    assert_true(not sub.is_visible(), "a closed menu group shows its entries")
    link.click()
    raw_page.wait_for_timeout(500)  # the 15.9 menu slides
    assert_true("menu-open" in (group.get_attribute("class") or ""), "menu group did not open")
    assert_true(sub.is_visible(), "an opened menu group hides its entries")
    link.click()
    raw_page.wait_for_timeout(500)
    assert_true("menu-open" not in (group.get_attribute("class") or ""), "menu group did not close")

    toggle = raw_page.locator('[data-widget="pushmenu"]').first
    open_width = _sidebar_width(raw_page)
    assert_true(open_width > 100, f"the side menu is not open on load (width {open_width})")
    toggle.click()
    raw_page.wait_for_timeout(500)
    assert_true(_sidebar_width(raw_page) < open_width, "the side menu did not collapse")
    toggle.click()
    raw_page.wait_for_timeout(500)
    assert_equal(_sidebar_width(raw_page), open_width, "the side menu did not come back to its width")


def _check_narrow_screen(raw_page, context: FessContext) -> None:
    raw_page.set_viewport_size({"width": 390, "height": 800})
    raw_page.goto(context.url("/admin/webconfig/"))
    raw_page.wait_for_load_state("domcontentloaded")
    assert_true(_sidebar_width(raw_page) < 1, "the side menu is open on a phone-sized screen")
    overflow = raw_page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    assert_true(overflow <= 1, f"the page scrolls sideways by {overflow}px on a phone-sized screen")
    raw_page.locator('[data-widget="pushmenu"]').first.click()
    raw_page.wait_for_timeout(400)  # the menu slides in
    assert_true(_sidebar_width(raw_page) > 100, "the side menu did not open")


def _check_date_range(raw_page, context: FessContext) -> None:
    raw_page.goto(context.url("/admin/searchlog/logs/"))
    raw_page.wait_for_load_state("domcontentloaded")
    field = raw_page.locator("#requestedTimeRangeSearch")

    if not raw_page.evaluate("typeof window.FessAdmin !== 'undefined'"):
        # the console of 15.9 and earlier: a text field with a date range picker
        assert_true(field.is_visible(), "the date range field is not shown")
        return

    inputs = raw_page.locator(".range-picker input[type=datetime-local]")
    assert_equal(inputs.count(), 2, "the date range is not two date-time inputs")
    inputs.nth(0).fill("2026-11-01T09:30")
    inputs.nth(1).fill("2026-11-19T18:05")
    assert_equal(field.input_value(), "2026-11-01 09:30 - 2026-11-19 18:05",
                  "the date range text the server reads is not composed from the inputs")

    raw_page.locator("section.content button[name=search]").first.click()
    raw_page.wait_for_load_state("domcontentloaded")
    text = raw_page.locator("#requestedTimeRangeSearch").input_value()
    assert_true(RANGE_TEXT.match(text), f"the date range did not survive the search: {text!r}")
    restored = raw_page.locator(".range-picker input[type=datetime-local]")
    assert_equal(restored.nth(0).input_value(), "2026-11-01T09:30", "the start was not restored")
    assert_equal(restored.nth(1).input_value(), "2026-11-19T18:05", "the end was not restored")


def _check_form_layout(raw_page, context: FessContext) -> None:
    raw_page.set_viewport_size({"width": 1280, "height": 900})
    raw_page.goto(context.url("/admin/webconfig/createnew/"))
    raw_page.wait_for_load_state("domcontentloaded")
    if not raw_page.evaluate("typeof window.FessAdmin !== 'undefined'"):
        return  # the console of 15.9 and earlier has no tabs

    links = raw_page.locator(".form-tabs .nav-link")
    assert_true(links.count() >= 2, "the crawl config form is not split into tabs")
    assert_true(raw_page.locator("#name").is_visible(), "the first tab does not show the name")
    assert_true(not raw_page.locator("#numOfThread").is_visible(), "a field of another tab is shown")
    links.nth(2).click()
    assert_true(raw_page.locator("#numOfThread").is_visible(), "the tab did not show its fields")
    assert_true(not raw_page.locator("#name").is_visible(), "the first tab stays open after another is chosen")
    threads = raw_page.locator("#numOfThread").bounding_box()
    interval = raw_page.locator("#intervalTime").bounding_box()
    assert_true(abs(threads["y"] - interval["y"]) < 4, "short fields are not side by side")

    raw_page.goto(context.url("/admin/systeminfo/"))
    raw_page.wait_for_load_state("domcontentloaded")
    assert_true(raw_page.locator("#envData").is_visible(), "the first system info tab is not open")
    assert_true(not raw_page.locator("#propData").is_visible(), "a system info tab is open that was not chosen")
    raw_page.locator("#systeminfo-prop-tab").click()
    assert_true(raw_page.locator("#propData").is_visible(), "the system properties tab did not open")
    assert_true(not raw_page.locator("#envData").is_visible(), "the first system info tab stays open")


def run(context: FessContext) -> None:
    logger.info("Starting admin_shell")
    raw_page = (context.get_wrapped_page() or context.get_admin_page())._page
    original_viewport = raw_page.viewport_size
    try:
        _check_assets_and_scripts(raw_page, context)
        _check_side_menu(raw_page, context)
        _check_narrow_screen(raw_page, context)
        _check_date_range(raw_page, context)
        _check_form_layout(raw_page, context)
    finally:
        # the page is shared with the modules that run after this one
        if original_viewport:
            raw_page.set_viewport_size(original_viewport)
    logger.info("admin_shell completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
