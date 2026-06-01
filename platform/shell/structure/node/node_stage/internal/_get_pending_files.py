from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DIR_STAGE_PENDING


def _get_pending_files(node_stage) -> list[PathType]:
    pending_dir = node_stage._stage_dir / DIR_STAGE_PENDING
    if not Path.exists(pending_dir):
        return []
    return [f for f in Path.iterdir(pending_dir) if Path.is_file(f)]
