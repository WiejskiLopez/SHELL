"""sub_node_command.py
SubNodeCommand — builds and holds the subprocess command for a graph node.

Slots:
    _app     — parent App
    _command — built command list (list[str] | None)
"""

from __future__ import annotations

from shell.structure.sub_node.sub_node_command.internal._assert_sub_node_command_set import _assert_sub_node_command_set
from shell.structure.sub_node.sub_node_command.internal._init_sub_node_command import _init_sub_node_command
from shell.component.command.command import Command


class SubNodeCommand:
    """Builds and holds the subprocess command for a single graph node."""

    __slots__ = ("_app", "_command",)

    def __init__(self, app=None) -> None:
        self._app = app
        self._command: Command | None = None

    @property
    def command_(self) -> Command:
        _assert_sub_node_command_set(self._command)
        return self._command

    def init_sub_node_command(self, sub_node_configuration, task_dir, python_exe=None) -> None:
        _init_sub_node_command(self, sub_node_configuration, task_dir, python_exe)
