from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _save_stage_done(stage_done, file: PathType) -> None:
    dest = stage_done.done_dir_ / file.name
    Path.copy_to(file, dest)
