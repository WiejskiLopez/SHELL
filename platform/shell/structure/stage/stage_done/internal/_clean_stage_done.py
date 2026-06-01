from __future__ import annotations

from shell.utils.path.path import Path


def _clean_stage_done(stage_done) -> None:
    done_dir = stage_done.done_dir_
    if not Path.exists(done_dir):
        return
    for item in Path.iterdir(done_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
