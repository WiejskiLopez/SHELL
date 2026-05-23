from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _get_stage_pending_files(stage_pending) -> list[PathType]:
    pending_dir = stage_pending.pending_dir_
    if not Path.exists(pending_dir):
        return []
    return [f for f in Path.iterdir(pending_dir) if Path.is_file(f)]
