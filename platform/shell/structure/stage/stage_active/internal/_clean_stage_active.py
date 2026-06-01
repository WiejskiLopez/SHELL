from __future__ import annotations

from shell.utils.path.path import Path


def _clean_stage_active(stage_active) -> None:
    active_dir = stage_active.active_dir_
    if not Path.exists(active_dir):
        return
    for item in Path.iterdir(active_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
