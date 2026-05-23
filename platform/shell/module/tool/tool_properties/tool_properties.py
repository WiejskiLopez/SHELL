"""tool_properties.py
ToolProperties — placeholder for future tool execution parameters.
"""

from __future__ import annotations


class ToolProperties:
    """Holds Tool runtime parameters extracted from YAML config."""

    __slots__ = ("_app",)

    def __init__(self, app) -> None:
        self._app = app

    def init_tool_properties(self) -> None:
        pass
