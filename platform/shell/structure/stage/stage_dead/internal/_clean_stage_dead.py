from __future__ import annotations

from shell.utils.path.path import Path


def _clean_stage_dead(stage_dead) -> None:
    dead_dir = stage_dead.dead_dir_
    if not Path.exists(dead_dir):
        return
    for item in Path.iterdir(dead_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
