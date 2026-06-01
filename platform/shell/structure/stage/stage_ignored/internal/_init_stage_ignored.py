from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_STAGE, DIR_STAGE_IGNORED


def _init_stage_ignored(stage_ignored) -> None:
    stage_ignored._ignored_dir = stage_ignored._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_STAGE / DIR_STAGE_IGNORED
    Path.mkdir(stage_ignored.ignored_dir_)
