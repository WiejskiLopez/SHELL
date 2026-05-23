from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _save_stage_active(stage_active, file: PathType, dest_name: str | None = None) -> None:
    name = dest_name if dest_name is not None else file.name
    dest = stage_active.active_dir_ / name
    Path.copy_to(file, dest)
