from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_OUTPUT


def _has_own_output(app) -> bool:
    output_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_OUTPUT
    return Path.exists(output_dir) and any(Path.iterdir(output_dir))
