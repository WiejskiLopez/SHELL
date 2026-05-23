"""runner_properties.py
RunnerProperties — runtime execution parameters for the runner.

Slots:
    add_dirs — list of extra directories passed via --add-dir CLI flags
"""

from __future__ import annotations


class RunnerProperties:
    """Holds runner-level execution parameters."""

    __slots__ = ("_add_dirs",)

    def __init__(self) -> None:
        self._add_dirs: list[str] | None = None

    @property
    def add_dirs_(self) -> list[str]:
        """Return add_dirs list (empty list when not set)."""
        return self._add_dirs or []
