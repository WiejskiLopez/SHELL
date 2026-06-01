from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _save_stage_history(stage_history, file: PathType) -> None:
    dest = stage_history.history_dir_ / file.name
    Path.copy_to(file, dest)
