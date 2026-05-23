"""node_input.py
NodeInput: single entry point for reading node input files.

Fields (own):
    input_dir     — path to the input directory (Path)
    input_message — MessageList of loaded messages
    _module_status — ModuleStatus enum; NEW on construction, INIT after init_node_input()

Methods:
    init_node_input() — load all *.yaml files from input_dir into input_message
"""

from __future__ import annotations


from shell.component.message.message_list.message_list import MessageList
from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_input.internal._init_node_input import _init_node_input
from shell.utils.path.path import Path, PathType


class NodeInput:
    """Manages reading of input files for a single node run.

    input_dir must be set before calling init_node_input.
    init_node_input loads all *.yaml files from input_dir into input_message.
    """

    __slots__ = ("_app", "_input_dir", "_module_status", "_input_message")

    def __init__(self, app) -> None:
        self._app = app
        self._input_dir: PathType | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW
        self._input_message: MessageList | None = None

    # -----------------------------------------------------------------------
    # Validated properties
    # -----------------------------------------------------------------------

    @property
    def input_message_(self) -> MessageList:
        return self._input_message

    @property
    def input_dir_(self) -> PathType:
        return self._input_dir

    @property
    def input_files_map_(self) -> dict[File, str]:
        """Return mapping of loaded File objects to their file names."""
        return self._input_files_map

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_node_input(self) -> None:
        _init_node_input(self)
        self._module_status = ModuleStatus.INIT

    def clean_node_input(self) -> None:
        target = self._input_dir
        if not Path.exists(target):
            return
        for item in Path.iterdir(target):
            try:
                if Path.is_file(item) or Path.is_symlink(item):
                    Path.unlink(item)
                elif Path.is_dir(item):
                    Path.rmtree(item)
            except OSError:
                pass
