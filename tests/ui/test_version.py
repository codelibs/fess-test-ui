"""Tests for the Fess version switch between the JSP and static-theme modules.

Picking the wrong line would not fail loudly in a Docker run: it would report
every search module as a broken UI. The parsing and the dispatch are pure
Python, so they are pinned here.
"""
from types import SimpleNamespace

import pytest

from fess.test.ui import version


@pytest.fixture(autouse=True)
def _forget_version(monkeypatch):
    monkeypatch.setattr(version, "_version", None)


class _FakeContext:
    def url(self, path: str) -> str:
        return f"http://fess{path}"


class _FakeResponse:
    def __init__(self, status_code: int, body):
        self.status_code = status_code
        self._body = body

    def json(self):
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


def _serve(monkeypatch, status_code, body):
    calls = []

    def fake_get(url, timeout):
        calls.append(url)
        return _FakeResponse(status_code, body)

    monkeypatch.setattr(version.requests, "get", fake_get)
    return calls


def _api_result(ver: str) -> dict:
    return {"response": {"message": "Unauthorized request.",
                         "version": ver, "status": 3}}


class _JspModule:
    __name__ = "fess.test.ui.search.example_jsp"

    def __init__(self):
        self.ran = []

    def run(self, context):
        self.ran.append(context)


@pytest.mark.parametrize("text,expected", [
    ("15.8", (15, 8)),
    ("15.9", (15, 9)),
    ("15.9.0", (15, 9)),
    ("15.9.0-SNAPSHOT", (15, 9)),
    ("15.10", (15, 10)),
    ("16.0", (16, 0)),
])
def test_parse_version(text, expected):
    assert version.parse_version(text) == expected


@pytest.mark.parametrize("text", ["", None, "15", "snapshot", "v15.9", "159.x"])
def test_parse_version_rejects_non_versions(text):
    with pytest.raises(ValueError):
        version.parse_version(text)


def test_versions_compare_numerically_not_as_text():
    assert version.parse_version("15.10") >= version.STATIC_THEME_SINCE
    assert version.parse_version("15.8") < version.STATIC_THEME_SINCE
    assert version.parse_version("14.19") < version.STATIC_THEME_SINCE


def test_fess_version_reads_the_admin_api_envelope_once(monkeypatch):
    calls = _serve(monkeypatch, 401, _api_result("15.8"))
    context = _FakeContext()
    assert version.fess_version(context) == (15, 8)
    assert version.fess_version(context) == (15, 8)
    assert calls == ["http://fess" + version.VERSION_PATH]


@pytest.mark.parametrize("status_code,body", [
    (404, ValueError("Not Found.")),       # not JSON
    (200, {"response": {"status": 0}}),    # no version
    (200, {"status": 0}),                  # no envelope
    (200, ["15.9"]),                       # not an object
    (401, _api_result("unknown")),         # not a version
])
def test_fess_version_raises_instead_of_guessing(monkeypatch, status_code, body):
    _serve(monkeypatch, status_code, body)
    with pytest.raises((RuntimeError, ValueError)):
        version.fess_version(_FakeContext())
    assert version._version is None


@pytest.mark.parametrize("ver", ["15.8", "14.19"])
def test_run_jsp_variant_runs_the_jsp_module_before_15_9(monkeypatch, ver):
    _serve(monkeypatch, 401, _api_result(ver))
    context = _FakeContext()
    jsp = _JspModule()
    assert version.run_jsp_variant(context, jsp) is True
    assert jsp.ran == [context]


@pytest.mark.parametrize("ver", ["15.9", "15.10", "16.0"])
def test_run_jsp_variant_leaves_15_9_and_later_to_the_caller(monkeypatch, ver):
    _serve(monkeypatch, 401, _api_result(ver))
    jsp = _JspModule()
    assert version.run_jsp_variant(_FakeContext(), jsp) is False
    assert jsp.ran == []


def test_run_jsp_variant_propagates_a_failed_detection(monkeypatch):
    _serve(monkeypatch, 404, ValueError("Not Found."))
    jsp = _JspModule()
    with pytest.raises(RuntimeError):
        version.run_jsp_variant(_FakeContext(), jsp)
    assert jsp.ran == []


def test_every_switched_module_has_its_jsp_variant():
    """Each module that dispatches names an importable <module>_jsp with a
    run(), so a typo cannot silently fall through to the SPA module."""
    import importlib
    import pathlib
    import re

    root = pathlib.Path(version.__file__).parent
    switched = []
    for path in sorted(root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for name in re.findall(r"run_jsp_variant\(context, (\w+)\)", text):
            switched.append(path)
            assert name == path.stem + "_jsp", path
            package = ".".join(path.relative_to(root.parent.parent.parent)
                               .with_suffix("").parts[:-1])
            module = importlib.import_module(f"{package}.{name}")
            assert callable(getattr(module, "run", None)), module
    assert len(switched) == 19
