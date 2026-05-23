from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_TEMP


def _init_temp_dir(node_temp) -> None:
    node_temp._temp_dir = (node_temp._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TEMP).resolve()
    Path.mkdir(node_temp.temp_dir_)
