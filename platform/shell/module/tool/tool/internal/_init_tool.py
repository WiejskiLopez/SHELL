"""_init_tool.py
Delegate initialization to tool_properties and tool_command.
"""

from __future__ import annotations


def _init_tool(tool, reader=None) -> None:
    app = tool._app

    try:
        tool.tool_properties_.init_tool_properties()
    except ValueError as exc:
        app.app_trace_.record_error_and_raise('tool._init_tool._init_tool', exc)
