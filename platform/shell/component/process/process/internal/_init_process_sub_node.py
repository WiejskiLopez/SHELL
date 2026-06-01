from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.component.process.process.process import Process


def _init_process_sub_node(process: 'Process', sub_node, task_dir, python_exe=None) -> None:
    process.process_command_.init_process_command_sub_node(sub_node, task_dir, process.app_, python_exe)
