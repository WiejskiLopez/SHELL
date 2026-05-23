from shell.utils.path.path import PathType
"""_build_log_path.py
Responsible for one thing: building the log file path inside the node logs/ directory.
Convention: logs/<role>.<YYYY-MM-DD_HH>.<level>.log_
"""

from datetime import datetime, timezone


def _build_log_path(node: PathType, log_level: str = "INFO", now: datetime = None, role: str = "agent") -> PathType:
    """Return logs/<role>.<YYYY-MM-DD_HH>.<level>.log_ inside node."""
    if now is None:
        now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d_%H")
    return node / ".node" / "logs" / f"{role}.{stamp}.{log_level.strip().lower()}.log"
