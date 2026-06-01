from __future__ import annotations


from shell.constants.constants import DIR_STAGE_ACTIVE, DIR_STAGE_PENDING, DIR_STAGE_HISTORY, DIR_STAGE_IGNORED, DIR_STAGE_DEAD, DIR_STAGE_DONE
from shell.utils.path.path import Path, PathType


def _init_stage_dirs(node_stage) -> None:
    stage_dir = node_stage._stage_dir
    for sub in (DIR_STAGE_ACTIVE, DIR_STAGE_PENDING, DIR_STAGE_HISTORY, DIR_STAGE_IGNORED, DIR_STAGE_DEAD, DIR_STAGE_DONE):
        Path.mkdir(stage_dir / sub)
