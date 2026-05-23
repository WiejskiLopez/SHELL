from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_SCRIPTS


def _init_scripts_dir(node_scripts) -> None:
    node_scripts._scripts_dir = (node_scripts._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_SCRIPTS).resolve()
    Path.mkdir(node_scripts.scripts_dir_)
