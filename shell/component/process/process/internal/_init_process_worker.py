from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.component.process.process.process import Process


def _init_process_worker(process: 'Process') -> None:
    app = process.app_
    app_properties = app.app_properties_
    cwd = str(app.app_node_.node_.node_dir_)
    if app_properties.type_ == 'python_module':
        cmd = [sys.executable, '-m', app_properties.command_]
    else:
        cmd = [app_properties.command_]
    process.process_command_.init_process_command(cmd=cmd, cwd=cwd, timeout=app_properties.timeout_)
