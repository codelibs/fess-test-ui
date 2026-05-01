"""Unit tests for `_normalize_text_selector`.

Background: Playwright's `text=Back` does case-insensitive substring match,
so it picks up `<p>Backup</p>` as well as the actual Back button. The English
labels `crud_button_back="Back"` and `menu_backup="Backup"` collide. Quoting
(`text="Back"`) forces exact match and resolves the collision.

The helper rewrites unquoted `text=...` selectors to the quoted form, leaves
already-quoted, regex, and non-text selectors alone, and preserves chained
selectors (`text=X >> css=...`).
"""
from fess.test.ui.context import _normalize_text_selector


def test_quotes_unquoted_text_selector():
    assert _normalize_text_selector("text=Back") == 'text="Back"'


def test_leaves_already_double_quoted_alone():
    assert _normalize_text_selector('text="Back"') == 'text="Back"'


def test_leaves_already_single_quoted_alone():
    assert _normalize_text_selector("text='Back'") == "text='Back'"


def test_leaves_regex_text_alone():
    assert _normalize_text_selector("text=/^Back$/") == "text=/^Back$/"


def test_leaves_non_text_selector_alone():
    assert _normalize_text_selector('button:has-text("Back")') == 'button:has-text("Back")'
    assert _normalize_text_selector('[placeholder="ユーザー名"]') == '[placeholder="ユーザー名"]'
    assert _normalize_text_selector("input[name=\"name\"]") == "input[name=\"name\"]"


def test_leaves_chained_selector_alone():
    """Chained `text=X >> ...` selectors deliberately use substring matching
    (e.g. `text=キャンセル 削除 >> button[name="delete"]` finds a dialog
    containing both words and then drills into a button). Forcing exact match
    here would break the query, so leave chained selectors untouched.
    """
    assert (
        _normalize_text_selector('text=キャンセル 削除 >> button[name="delete"]')
        == 'text=キャンセル 削除 >> button[name="delete"]'
    )


def test_handles_japanese_label():
    assert _normalize_text_selector("text=戻る") == 'text="戻る"'


def test_handles_label_with_spaces():
    assert _normalize_text_selector("text=Bad Words") == 'text="Bad Words"'


def test_handles_label_with_slash():
    """labels.menu_data = 'Backup/Restore' — slashes must survive quoting."""
    assert _normalize_text_selector("text=Backup/Restore") == 'text="Backup/Restore"'


def test_escapes_embedded_double_quote():
    """If a label literally contains a `"`, escape it to keep the wrapping valid."""
    assert _normalize_text_selector('text=Say "hi"') == 'text="Say \\"hi\\""'


def test_empty_selector_unchanged():
    assert _normalize_text_selector("") == ""
