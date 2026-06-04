from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_INPUT


def _has_own_input(app) -> bool:
    input_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_INPUT
    return Path.exists(input_dir) and any(Path.iterdir(input_dir))
