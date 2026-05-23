"""_is_stale.py
Private. Responsible for one thing: determining whether a lock file is stale
(i.e. the owning process no longer exists).
"""

import json

from shell.component.locker.internal._pid_alive import _pid_alive
from shell.utils.path.path import Path, PathType


def _is_stale(lock_path: PathType) -> bool:
    try:
        data = json.loads(Path.read_text(lock_path))
    except (OSError, ValueError):
        return False
    pid = data.get("pid")
    if not isinstance(pid, int) or pid <= 0:
        return True
    return not _pid_alive(pid)
