"""node_output.py
NodeOutput: single entry point for writing node output files.

Fields (own):
    output_dir       — path to the output directory (path)
    output_files_map — dict[File, str] mapping each File to its file_name
    _module_status   — ModuleStatus enum; NEW on construction, INIT after init_node_output()

Methods:
    init_node_output() — mark module as initialised
    save_output() — save all files from output_files_map to output_dir
"""

from __future__ import annotations

from shell.utils.path.path import PathType


from shell.component.message.message_list.message_list import MessageList
from shell.utils.file.File import File
from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_output.internal._assert_output_dir_exists import _assert_output_dir_exists
from shell.structure.node.node_output.internal._clean_node_output import _clean_node_output
from shell.structure.node.node_output.internal._init_node_output import _init_node_output
from shell.structure.node.node_output.internal._format_node_output import _format_node_output

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.app.app.app import App


class NodeOutput:
    """Manages writing of output files for a single node run.

    output_dir must exist before calling save_output.
    save_output writes all File objects from output_files_map to output_dir.
    """

    __slots__ = ("_app", "_output_dir", "_output_files_map", "_module_status", "_output_message")

    def __init__(self, app: 'App') -> None:
        self._app = app
        self._output_dir: PathType | None = None
        self._output_files_map: dict[File, str] = {}
        self._module_status: ModuleStatus = ModuleStatus.NEW
        self._output_message: MessageList | None = None

    # -----------------------------------------------------------------------
    # Validated properties
    # -----------------------------------------------------------------------

    @property
    def output_message_(self) -> MessageList:
        return self._output_message

    @property
    def output_dir_(self) -> PathType:
        return self._output_dir

    @property
    def output_files_map_(self) -> dict[File, str]:
        """Return mapping of File objects to their file names."""
        return self._output_files_map

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_node_output(self) -> None:
        _init_node_output(self)
        self._module_status = ModuleStatus.INIT

    def save_output(self) -> None:
        """Save all files from output_files_map to output_dir.

        output_files_map — dict mapping File -> file_name (str).
        Each File is saved under output_dir / file_name.
        """
        output_dir = self.output_dir_
        for file, file_name in self._output_files_map.items():
            file._file_path = output_dir / file_name
            file.save_file()

    def clean_node_output(self) -> None:
        _clean_node_output(self)

    def format_node_output(self) -> None:
        _format_node_output(self)
