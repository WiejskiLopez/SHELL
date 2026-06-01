from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_STAGE, DIR_STAGE_DONE


def _init_stage_done(stage_done) -> None:
    stage_done._done_dir = stage_done._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_STAGE / DIR_STAGE_DONE
    Path.mkdir(stage_done.done_dir_)
