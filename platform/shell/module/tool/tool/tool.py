"""tool.py
Tool — wrapper for external tools in a graph node.

Tools are extra apps that do NOT generate working logs (unlike scripts/workers).

Responsibilities:
    init_tool()   — validate tool fields from node_config
    run_tool()    — build command, run subprocess, return Status
"""

from __future__ import annotations

from collections.abc import Callable
from subprocess import CompletedProcess

from shell.module.tool.tool.internal._init_tool import _init_tool
from shell.module.tool.tool.internal._run_tool import _run_tool
from shell.status.status import Status
from shell.module.tool.tool_properties.tool_properties import ToolProperties


class Tool:
    """Runs an external tool process for a single graph node."""

    __slots__ = ("_app", "_tool_properties")

    def __init__(self, app) -> None:
        self._app = app
        self._tool_properties: ToolProperties | None = None

    def init_tool(self, reader=None) -> None:
        _init_tool(self, reader=reader)

    def run_tool(
        self,
        runner: Callable[..., CompletedProcess] | None = None,
    ) -> Status:
        return _run_tool(self, runner=runner)

    @property
    def tool_properties_(self) -> ToolProperties:
        if self._tool_properties is None:
            self._tool_properties = ToolProperties(self._app)
        return self._tool_properties
