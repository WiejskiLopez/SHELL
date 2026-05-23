from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE

if TYPE_CHECKING:
    from shell.app.app_trace.app_trace import AppTrace

_DOT_NODE_DIRS = ("input", "output", "archive", "temp", "logs", "config", "scripts")


def _create_node(node_dir: PathType, make_dirs: Callable[[PathType], None], trace: 'AppTrace | None' = None) -> None:
    dot_node = node_dir / DOT_NODE
    for sub in _DOT_NODE_DIRS:
        path = dot_node / sub
        make_dirs(path)
        if not Path.exists(path):
            raise RuntimeError(f'[node._create_node] failed to create directory: {path}')
        # if trace is not None:
        #     trace.record_info('node._create_node._create_node', f'mkdir {path}')
