from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _save_stage_pending(stage_pending, file: PathType) -> None:
    dest = stage_pending.pending_dir_ / file.name
    Path.copy_to(file, dest)
