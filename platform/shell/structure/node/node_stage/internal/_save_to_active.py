from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DIR_STAGE_ACTIVE


def _save_to_active(node_stage, file: PathType, dest_name: str | None = None) -> None:
    name = dest_name if dest_name is not None else file.name
    dest = node_stage._stage_dir / DIR_STAGE_ACTIVE / name
    Path.copy_to(file, dest)
