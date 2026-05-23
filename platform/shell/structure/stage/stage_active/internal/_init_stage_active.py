from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_STAGE, DIR_STAGE_ACTIVE


def _init_stage_active(stage_active) -> None:
    stage_active._active_dir = stage_active._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_STAGE / DIR_STAGE_ACTIVE
    Path.mkdir(stage_active.active_dir_)
