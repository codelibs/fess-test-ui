"""
Enhanced assertion functions with logging support.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _truncate_value(value: Any, max_length: int = 100) -> str:
    """
    Truncate a value for display in logs.

    Args:
        value: Value to truncate
        max_length: Maximum string length

    Returns:
        Truncated string representation
    """
    str_value = str(value)
    if len(str_value) > max_length:
        return str_value[:max_length] + '...'
    return str_value


def assert_equal(first: Any, second: Any, msg: str = None) -> None:
    """
    Assert that two values are equal.

    Args:
        first: First value
        second: Second value
        msg: Optional custom message
    """
    result = first == second

    first_display = _truncate_value(first)
    second_display = _truncate_value(second)

    if result:
        logger.debug(f"[ASSERT] PASS: {first_display} == {second_display}")
    else:
        logger.warning(f"[ASSERT] FAIL: {first_display} != {second_display}")

    if msg is None:
        assert result, f"Expected {first_display} == {second_display}"
    else:
        assert result, msg


def assert_not_equal(first: Any, second: Any, msg: str = None) -> None:
    """
    Assert that two values are not equal.

    Args:
        first: First value
        second: Second value
        msg: Optional custom message
    """
    result = first != second

    first_display = _truncate_value(first)
    second_display = _truncate_value(second)

    if result:
        logger.debug(f"[ASSERT] PASS: {first_display} != {second_display}")
    else:
        logger.warning(f"[ASSERT] FAIL: {first_display} == {second_display}")

    if msg is None:
        assert result, f"Expected {first_display} != {second_display}"
    else:
        assert result, msg


def assert_startswith(first: str, second: str, msg: str = None) -> None:
    """
    Assert that a string starts with a prefix.

    Args:
        first: String to check
        second: Expected prefix
        msg: Optional custom message
    """
    result = first.startswith(second)

    first_display = _truncate_value(first)
    second_display = _truncate_value(second)

    if result:
        logger.debug(f"[ASSERT] PASS: '{first_display}' starts with '{second_display}'")
    else:
        logger.warning(f"[ASSERT] FAIL: '{first_display}' does not start with '{second_display}'")

    if msg is None:
        assert result, f"Expected '{first_display}' to start with '{second_display}'"
    else:
        assert result, msg


def assert_contains(container: Any, item: Any, msg: str = None) -> None:
    """
    Assert that a container contains an item.

    Args:
        container: Container (list, string, dict, etc.)
        item: Item to find
        msg: Optional custom message
    """
    result = item in container

    container_display = _truncate_value(container)
    item_display = _truncate_value(item)

    if result:
        logger.debug(f"[ASSERT] PASS: '{item_display}' found in container")
    else:
        logger.warning(f"[ASSERT] FAIL: '{item_display}' not found in container")

    if msg is None:
        assert result, f"Expected '{item_display}' to be in {container_display}"
    else:
        assert result, msg


def assert_true(value: Any, msg: str = None) -> None:
    """
    Assert that a value is truthy.

    Args:
        value: Value to check
        msg: Optional custom message
    """
    result = bool(value)

    if result:
        logger.debug("[ASSERT] PASS: value is truthy")
    else:
        logger.warning(f"[ASSERT] FAIL: value is falsy: {_truncate_value(value)}")

    if msg is None:
        assert result, f"Expected truthy value, got {_truncate_value(value)}"
    else:
        assert result, msg
