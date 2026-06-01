from __future__ import annotations

from shell.utils.path.path import Path


def _clean_stage_pending(stage_pending) -> None:
    pending_dir = stage_pending.pending_dir_
    if not Path.exists(pending_dir):
        return
    for item in Path.iterdir(pending_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
