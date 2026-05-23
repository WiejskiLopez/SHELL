from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_STAGE, DIR_STAGE_DEAD


def _init_stage_dead(stage_dead) -> None:
    stage_dead._dead_dir = stage_dead._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_STAGE / DIR_STAGE_DEAD
    Path.mkdir(stage_dead.dead_dir_)
