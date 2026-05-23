from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DIR_STAGE_DONE


def _get_last_message(node_stage) -> PathType | None:
    done_dir = node_stage._stage_dir / DIR_STAGE_DONE
    if not Path.exists(done_dir):
        return None
    candidates = [f for f in Path.iterdir(done_dir) if Path.is_file(f)]
    if not candidates:
        return None
    return max(candidates, key=lambda f: f.stat().st_mtime)
