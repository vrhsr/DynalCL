"""Shared assertion helper: show the check's details when it fails."""


def assert_check(result):
    details = {k: v for k, v in result.details.items() if k not in ("rows", "table")}
    assert result.passed, f"{result.name} failed: {details}"
    return result
