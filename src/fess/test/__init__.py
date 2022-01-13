
from typing import Any


def assert_equal(first: Any, second: Any, msg: str = None) -> None:
    if msg is None:
        assert first == second, f"{first} == {second}"
    else:
        assert first == second, msg


def assert_not_equal(first: Any, second: Any, msg: str = None) -> None:
    if msg is None:
        assert first != second, f"{first} != {second}"
    else:
        assert first == second, msg


def assert_startswith(first: str, second: str, msg: str = None) -> None:
    if msg is None:
        assert first.startswith(second), f"{first} == {second}"
    else:
        assert first.startswith(second), msg
