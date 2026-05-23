from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_STAGE, DIR_STAGE_HISTORY


def _init_stage_history(stage_history) -> None:
    stage_history._history_dir = stage_history._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_STAGE / DIR_STAGE_HISTORY
    Path.mkdir(stage_history.history_dir_)
