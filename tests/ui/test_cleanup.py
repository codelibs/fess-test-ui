"""Tests for the cleanup escalation guard.

The guard decides whether a leaked test record reddens its module or stays a
log line, and it does so from inside a `finally` block where getting it wrong
means masking the real failure. That logic is pure Python, so it is pinned here
rather than only in a Docker run.
"""
import re

import pytest

from fess.test.ui.cleanup import (MAX_DELETE_ITERATIONS, Cleanup, CleanupError,
                                  assert_absent, delete_by_name)


class _FakePage:
    """Minimal stand-in for the bits of playwright's Page that cleanup uses."""

    def __init__(self, text: str):
        self._text = text

    def inner_text(self, selector: str) -> str:
        return self._text


class _FakeContext:
    def url(self, path: str) -> str:
        return f"http://fess{path}"


class _FakeLocator:
    def __init__(self, page: "_FakeListPage", name: str):
        self._page = page
        self._name = name

    def count(self) -> int:
        return self._page.rows.count(self._name)

    @property
    def first(self) -> "_FakeLocator":
        return self

    def click(self) -> None:
        self._page.selected = self._name


class _FakeListPage:
    """An admin list page with rows that the delete flow actually removes.

    Models the real flow: clicking the row opens its details, and it is the
    modal-footer button that deletes. `deletes` = False makes every delete a
    no-op, which is how a non-progressing loop is exercised.
    """

    ROW_RE = re.compile(r'tr:has-text\("(.*)"\)')

    def __init__(self, rows: list, deletes: bool = True):
        self.rows = list(rows)
        self.deletes = deletes
        self.selected = None
        self.gotos = 0

    def goto(self, url: str) -> None:
        self.gotos += 1

    def wait_for_load_state(self, state: str) -> None:
        pass

    def locator(self, selector: str) -> _FakeLocator:
        return _FakeLocator(self, self.ROW_RE.search(selector).group(1))

    def click(self, selector: str) -> None:
        if 'name="delete"' in selector and self.deletes and self.selected in self.rows:
            self.rows.remove(self.selected)

    def inner_text(self, selector: str) -> str:
        return "\n".join(self.rows)


@pytest.fixture(autouse=True)
def _no_i18n(monkeypatch):
    """delete_by_name resolves the Delete button's label through t(), which
    needs an initialized bundle. The loop is what is under test here."""
    monkeypatch.setattr("fess.test.ui.cleanup.t", lambda key: "Delete")


def test_no_leaks_does_not_raise():
    cleanup = Cleanup()
    with cleanup.guard("nothing"):
        pass
    cleanup.escalate()


def test_leak_escalates_when_the_test_body_passed():
    cleanup = Cleanup()
    with cleanup.guard("role 'r1'"):
        raise AssertionError("r1 is still listed")

    with pytest.raises(CleanupError) as excinfo:
        cleanup.escalate()
    assert "r1 is still listed" in str(excinfo.value)


def test_guard_records_a_failed_assertion_instead_of_swallowing_it():
    """The defect this module exists to prevent: AssertionError is an
    Exception, so a bare `except Exception` around a cleanup assertion eats it
    and the module still passes."""
    cleanup = Cleanup()
    with cleanup.guard("user 'u1'"):
        raise AssertionError("u1 is still listed")
    with pytest.raises(CleanupError):
        cleanup.escalate()


def test_guard_lets_the_body_run_to_completion_when_it_succeeds():
    cleanup = Cleanup()
    ran = []
    with cleanup.guard("group 'g1'"):
        ran.append("deleted")
    assert ran == ["deleted"]
    cleanup.escalate()


def test_each_guard_is_independent():
    """A leaked user must not stop the group and role below it being cleaned."""
    cleanup = Cleanup()
    cleaned = []

    with cleanup.guard("user 'u1'"):
        raise AssertionError("u1 is still listed")
    with cleanup.guard("group 'g1'"):
        cleaned.append("g1")
    with cleanup.guard("role 'r1'"):
        cleaned.append("r1")

    assert cleaned == ["g1", "r1"]
    with pytest.raises(CleanupError):
        cleanup.escalate()


def test_all_leaks_are_named_in_the_escalation():
    cleanup = Cleanup()
    for name in ("u1", "g1"):
        with cleanup.guard(f"record {name!r}"):
            raise AssertionError(f"{name} is still listed")

    with pytest.raises(CleanupError) as excinfo:
        cleanup.escalate()
    message = str(excinfo.value)
    assert "u1" in message and "g1" in message
    assert "2 cleanup step(s)" in message


def test_leak_does_not_mask_an_original_failure():
    """The crux: escalating from `finally` would replace the in-flight
    exception, and main.run_module() reports only that, never __context__."""
    with pytest.raises(ValueError, match="the real failure"):
        try:
            raise ValueError("the real failure")
        finally:
            cleanup = Cleanup()
            with cleanup.guard("role 'r1'"):
                raise AssertionError("r1 is still listed")
            cleanup.escalate()


def test_leak_escalates_from_finally_when_the_body_passed():
    """Same shape as the module above it, minus the original failure."""
    with pytest.raises(CleanupError):
        try:
            pass
        finally:
            cleanup = Cleanup()
            with cleanup.guard("role 'r1'"):
                raise AssertionError("r1 is still listed")
            cleanup.escalate()


def test_a_swallowed_guard_does_not_look_like_a_propagating_failure():
    """`guard` catches, so exc_info is non-None *inside* its except block. If
    escalate() read it there it would never fire. It must see the restored
    value once the guard has exited."""
    cleanup = Cleanup()
    with cleanup.guard("first"):
        raise AssertionError("first leaked")
    with cleanup.guard("second"):
        raise AssertionError("second leaked")
    with pytest.raises(CleanupError):
        cleanup.escalate()


def test_keyboard_interrupt_is_not_filed_as_a_leak():
    """BaseException, not Exception: an interrupt must stop the run."""
    cleanup = Cleanup()
    with pytest.raises(KeyboardInterrupt):
        with cleanup.guard("role 'r1'"):
            raise KeyboardInterrupt()
    cleanup.escalate()


def test_cleanup_error_is_an_assertion_error():
    """main.run_module() files AssertionError as `failed` and everything else
    as `error`; a leak is a failed absence assertion."""
    assert issubclass(CleanupError, AssertionError)


def test_delete_by_name_deletes_the_row():
    page = _FakeListPage(["u1", "other"])
    delete_by_name(_FakeContext(), page, "/admin/user/", "u1")
    assert page.rows == ["other"]


def test_delete_by_name_loops_over_duplicates():
    """Fess never rejects duplicate names, and admin/webconfig's duplicate test
    deliberately creates two rows under one -- so deleting once is not enough."""
    page = _FakeListPage(["w1", "w1", "other"])
    delete_by_name(_FakeContext(), page, "/admin/webconfig/", "w1")
    assert page.rows == ["other"]


def test_delete_by_name_raises_when_nothing_matched():
    """The row is either beyond page 1 (leaked) or was never created. Both are
    real problems, so this raises rather than logging -- and escalate() stands
    down on the "never created" case, where a body failure is propagating."""
    page = _FakeListPage(["other"])
    with pytest.raises(CleanupError, match="beyond page 1"):
        delete_by_name(_FakeContext(), page, "/admin/user/", "u1")


def test_delete_by_name_raises_when_deleting_makes_no_progress():
    page = _FakeListPage(["u1"], deletes=False)
    with pytest.raises(CleanupError, match="delete attempts made no progress"):
        delete_by_name(_FakeContext(), page, "/admin/user/", "u1")


def test_delete_by_name_gives_up_rather_than_looping_forever():
    page = _FakeListPage(["u1"], deletes=False)
    with pytest.raises(CleanupError):
        delete_by_name(_FakeContext(), page, "/admin/user/", "u1")
    # One goto to open the list, then one per attempt before it gives up.
    assert page.gotos == MAX_DELETE_ITERATIONS + 1


def test_delete_by_name_leak_reddens_its_own_module():
    """The whole point: a leak that used to be a log line now fails the module
    that caused it."""
    page = _FakeListPage(["u1"], deletes=False)
    cleanup = Cleanup()
    with cleanup.guard("user 'u1'"):
        delete_by_name(_FakeContext(), page, "/admin/user/", "u1")
    with pytest.raises(CleanupError, match="the test passed but"):
        cleanup.escalate()


def test_delete_by_name_leak_does_not_mask_an_original_failure():
    page = _FakeListPage(["u1"], deletes=False)
    with pytest.raises(ValueError, match="the real failure"):
        try:
            raise ValueError("the real failure")
        finally:
            cleanup = Cleanup()
            with cleanup.guard("user 'u1'"):
                delete_by_name(_FakeContext(), page, "/admin/user/", "u1")
            cleanup.escalate()


def test_assert_absent_passes_when_the_row_is_gone():
    assert_absent(_FakePage("Create New\nsome other row"), "u1", "/admin/user/")


def test_assert_absent_is_red_when_the_row_survived():
    with pytest.raises(AssertionError, match="still listed"):
        assert_absent(_FakePage("Create New\nu1\nsome other row"), "u1",
                      "/admin/user/")


def test_assert_absent_inside_a_guard_becomes_a_leak():
    """The two halves joined: the absence check supplies the red input that
    `except Exception` used to eat."""
    cleanup = Cleanup()
    with cleanup.guard("user 'u1'"):
        assert_absent(_FakePage("u1"), "u1", "/admin/user/")
    with pytest.raises(CleanupError):
        cleanup.escalate()
