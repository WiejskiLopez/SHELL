from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DIR_STAGE_HISTORY


def _save_to_history(node_stage, file: PathType) -> None:
    dest = node_stage._stage_dir / DIR_STAGE_HISTORY / file.name
    Path.copy_to(file, dest)
