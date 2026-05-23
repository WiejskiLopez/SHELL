from __future__ import annotations

from shell.utils.path.path import Path


def _clean_node_logs(node_logs) -> None:
    logs_dir = node_logs.logs_dir_
    if not Path.exists(logs_dir):
        return
    for item in Path.iterdir(logs_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
