from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _get_stage_done_last_message(stage_done) -> PathType | None:
    done_dir = stage_done.done_dir_
    if not Path.exists(done_dir):
        return None
    candidates = [f for f in Path.iterdir(done_dir) if Path.is_file(f)]
    if not candidates:
        return None
    return max(candidates, key=lambda f: f.stat().st_mtime)
