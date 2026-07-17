"""Cleanup that reddens its own module when it leaks, without masking the
failure that got it there.

Cleanup runs in `finally`, and the obvious way to write it is wrong twice over:

    finally:
        try:
            ...click delete...
            assert_equal(page.url, context.url("/admin/user/"))
        except Exception as e:
            logger.error(f"LEAKED user {name}: {e}")

`assert_equal` raises AssertionError, which IS an Exception, so the `except`
eats the very assertion meant to catch the leak. The module still reports PASS
and the log at most whispers. (That particular assertion could not fail anyway:
LastaFlute lands on the same list URL whether or not the row was deleted.)

A leak that only logs does not stay harmless. A leaked admin user, a global
dictionary entry or an unrestored setting resurfaces LATER as a plausible red
in an unrelated module -- the suite then lies about which code is broken. So a
failed cleanup must redden the module that caused it.

It must not, however, mask the failure that got us into `finally`. Raising
there replaces the in-flight exception: the original survives only as
`__context__`, which main.run_module() never reports. Hence `escalate()`
re-raises only when no original exception is propagating.

`sys.exc_info()[0] is None` is that test. Measured, not assumed:

    - reached normally           -> None            -> escalate
    - reached while X propagates -> X               -> log only, X wins
    - after `guard` swallowed a cleanup error, exc_info is restored to
      whichever of the two above applies, so the guards do not fool the test.

Its one sharp edge: exc_info is per-thread and looks DOWN the stack, so a
caller sitting inside its own `except` block would read as "an exception is
propagating" and silently disable escalation. No caller does that today --
main.run_module() calls module.run() from a `try`, and every package composer
chains its leaves with no handler at all -- but that is the thing to re-check
if escalation ever goes quiet.
"""
import logging
import sys
from contextlib import contextmanager

from fess.test import assert_equal
from fess.test.i18n import t
from fess.test.i18n.keys import Labels

logger = logging.getLogger(__name__)

# Every admin list page renders its table inside section.content
# (admin_user.jsp, admin_dict_mapping.jsp, ... all carry exactly one).
# Deliberately not "table": a delete that empties the list can leave no table
# at all, and inner_text would then raise instead of reporting absence.
LIST_SECTION = "section.content"


class CleanupError(AssertionError):
    """A cleanup step left state behind on the shared Fess instance.

    Subclasses AssertionError so main.run_module() files it as `failed` rather
    than `error`: the proximate cause is a failed absence assertion -- the row
    is still there -- not a broken harness.
    """


def assert_absent(page, name: str, where: str) -> None:
    """Assert `name` is gone from the list page currently on screen.

    This is the only honest read of "was it deleted?" from the UI. Asserting
    page.url after a delete proves nothing -- LastaFlute redirects to the list
    on success and re-renders that same list URL on failure, byte-identical.

    The caller must already be on the right page: dictionary lists paginate and
    a new entry lands on the LAST page, so checking page 1 there would pass
    while the row sat two pages away.

    Safe against the success banner echoing the name back: every delete on
    these pages saves addSuccessCrudDeleteCrudTable(GLOBAL), whose text
    ("Deleted the data.") takes no arguments.
    """
    listed = page.inner_text(LIST_SECTION)
    assert_equal(listed.find(name), -1,
                 f"{name} is still listed at {where} after deleting it")


MAX_DELETE_ITERATIONS = 10


def delete_by_name(context, page, list_path: str, name: str) -> None:
    """Delete every row matching `name` on an admin list page.

    Loops rather than assuming a single match: Fess never rejects duplicate
    names, and admin/webconfig's duplicate-name test deliberately creates two
    rows under one, so a leaked name can appear more than once.

    Raises rather than logging. Call it inside `Cleanup.guard()`: the leak then
    reddens its own module, and `Cleanup.escalate()` keeps it from masking the
    failure that got you into `finally`.
    """
    page.goto(context.url(list_path))
    page.wait_for_load_state("domcontentloaded")

    row = f'table tr:has-text("{name}")'
    iterations = 0
    while page.locator(row).count() > 0:
        iterations += 1
        if iterations > MAX_DELETE_ITERATIONS:
            raise CleanupError(
                f"{name} is still listed at {list_path} after "
                f"{MAX_DELETE_ITERATIONS} delete attempts made no progress")
        page.locator(row).first.click()
        page.wait_for_load_state("domcontentloaded")
        page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
        page.click('div.modal-footer button[name="delete"]')
        page.wait_for_load_state("domcontentloaded")
        page.goto(context.url(list_path))
        page.wait_for_load_state("domcontentloaded")

    if iterations == 0:
        # count() only ever sees page 1 (paging.page.size = 25), so a row
        # pushed onto page 2 reads as "nothing to clean". Raising is safe
        # despite the "was it ever created?" ambiguity: a body that failed
        # before creating the record leaves an exception propagating, and
        # escalate() stands down for that case rather than masking it.
        raise CleanupError(
            f"nothing matched {name} at {list_path}: no such row on page 1, "
            f"so either it was never created or it is beyond page 1 and has "
            f"leaked onto this shared instance")

    assert_absent(page, name, list_path)


class Cleanup:
    """Collects cleanup failures in a `finally` block, then escalates.

    Usage -- construct in `finally`, guard each step, escalate once at the end:

        finally:
            cleanup = Cleanup()
            with cleanup.guard(f"role '{role_name}'"):
                ...delete it...
                assert_absent(page, role_name, "/admin/role/")
                logger.info(f"✓ Role '{role_name}' deleted")
            cleanup.escalate()

    Each guard is independent: a leaked user does not stop the group and role
    below it from being cleaned up too.
    """

    def __init__(self) -> None:
        self._leaks: list = []

    @contextmanager
    def guard(self, what: str):
        """Run one cleanup step. Record -- never swallow -- its failure.

        Catches Exception, not BaseException: a KeyboardInterrupt should still
        stop the run rather than be filed as a leak.
        """
        try:
            yield
        except Exception as e:
            logger.error(f"LEAKED {what} — will pollute later modules: {e}")
            self._leaks.append(f"{what}: {e}")

    def escalate(self) -> None:
        """Re-raise the collected leaks, unless a real failure is in flight."""
        if not self._leaks:
            return

        propagating = sys.exc_info()[0]
        if propagating is not None:
            logger.error(
                f"{len(self._leaks)} cleanup leak(s) NOT escalated: a "
                f"{propagating.__name__} is already propagating and reporting "
                f"it is more useful than reporting the wreckage it left. "
                f"Leaked: {'; '.join(self._leaks)}")
            return

        raise CleanupError(
            f"the test passed but {len(self._leaks)} cleanup step(s) leaked "
            f"state onto the shared instance, which would resurface as a "
            f"failure in some later, unrelated module: {'; '.join(self._leaks)}")
