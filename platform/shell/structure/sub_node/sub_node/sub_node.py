"""sub_node.py
SubNode: structured value object for a single graph node.

Slots:
    _app                  -- parent App (DOM back-reference)
    _sub_node_config      -- Config instance loaded from graph node entry
"""

from __future__ import annotations

from shell.utils.path.path import Path, PathType

from shell.utils.io.io import default_make_dirs, default_read_utf8, default_write_utf8
from shell.component.config.config.config import Config
from shell.structure.sub_node.sub_node.internal._assert_entrypoint_exists import _assert_entrypoint_exists
from shell.structure.sub_node.sub_node.internal._init_sub_node import _init_sub_node
from shell.structure.sub_node.sub_node.internal._run_sub_node import _run_sub_node
from shell.structure.sub_node.sub_node_command.sub_node_command import SubNodeCommand
from shell.structure.sub_node.sub_node_properties.sub_node_properties import SubNodeProperties
from shell.structure.node.node_status.node_status import NodeStatus
from shell.status.status import Status


class SubNode:
    """Structured value object for a single graph node."""

    __slots__ = ("_app", "_sub_node_config", "_sub_node_command", "_node_status", "_sub_node_properties")

    def __init__(self, app=None) -> None:
        self._app = app
        self._sub_node_config: Config | None = None
        self._sub_node_command: SubNodeCommand | None = None
        self._node_status: NodeStatus = NodeStatus(None)
        self._sub_node_properties: SubNodeProperties | None = None

    # deprecated
    @classmethod
    def from_dict(cls, d: dict, app=None) -> SubNode:
        return cls(app=app)

    # -----------------------------------------------------------------------
    # Node facade
    # -----------------------------------------------------------------------

    @property
    def sub_node_command_(self) -> SubNodeCommand:
        if self._sub_node_command is None:
            self._sub_node_command = SubNodeCommand(self._app)
        return self._sub_node_command

    @property
    def sub_node_properties_(self) -> SubNodeProperties:
        if self._sub_node_properties is None:
            self._sub_node_properties = SubNodeProperties(self._app)
        return self._sub_node_properties

    @property
    def node_status_(self) -> NodeStatus:
        return self._node_status

    @property
    def status_(self) -> Status | None:
        return self._node_status.status_

    @property
    def is_ready_(self) -> bool:
        return self._node_status.is_ready_

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    @property
    def node_name_(self) -> str:
        return self.sub_node_properties_.sub_node_name_

    @property
    def mode_(self) -> str | None:
        if self._sub_node_config is None:
            return None
        return self._sub_node_config.config_dict_.get('mode')

    @property
    def role_(self) -> str | None:
        if self._sub_node_config is None:
            return None
        return self._sub_node_config.config_dict_.get('role')

    @property
    def model_(self) -> str | None:
        if self._sub_node_config is None:
            return None
        return self._sub_node_config.config_dict_.get('model')

    @property
    def timeout_(self) -> int | None:
        if self._sub_node_config is None:
            return None
        return self._sub_node_config.config_dict_.get('timeout')

    @property
    def entrypoint_path_(self) -> PathType:
        path = Path.resolve(Path.new(self._sub_node_config.config_dict_['runner_root_dir'])) / 'entrypoint.py'
        _assert_entrypoint_exists(path)
        return Path.resolve(path)

    # -----------------------------------------------------------------------
    # Init
    # -----------------------------------------------------------------------

    def init_sub_node(
        self,
        sub_node_config_dict: dict,
        writer=None,
        reader=None,
    ) -> None:
        if writer is None:
            writer = default_write_utf8
        if reader is None:
            reader = default_read_utf8
        _init_sub_node(self, sub_node_config_dict, writer, reader)

    def init_sub_node_command(self, task_dir, python_exe=None) -> None:
        self.sub_node_command_.init_sub_node_command(
            self.sub_node_properties_,
            task_dir,
            python_exe,
        )

    def run_sub_node(self, task_dir, runner=None, python_exe=None) -> dict:
        return _run_sub_node(self, task_dir, self._app, runner=runner, python_exe=python_exe)