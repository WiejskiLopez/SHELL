from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DIR_STAGE_PENDING


def _save_to_pending(node_stage, file: PathType) -> None:
    dest = node_stage._stage_dir / DIR_STAGE_PENDING / file.name
    Path.copy_to(file, dest)
