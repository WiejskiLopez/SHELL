from __future__ import annotations

from shell.utils.path.path import Path


def _clean_stage_ignored(stage_ignored) -> None:
    ignored_dir = stage_ignored.ignored_dir_
    if not Path.exists(ignored_dir):
        return
    for item in Path.iterdir(ignored_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
