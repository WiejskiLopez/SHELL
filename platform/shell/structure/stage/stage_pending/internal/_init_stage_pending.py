from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_STAGE, DIR_STAGE_PENDING


def _init_stage_pending(stage_pending) -> None:
    stage_pending._pending_dir = stage_pending._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_STAGE / DIR_STAGE_PENDING
    Path.mkdir(stage_pending.pending_dir_)
