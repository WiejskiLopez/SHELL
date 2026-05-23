from __future__ import annotations

from shell.utils.path.path import Path


def _clean_node_temp(node_temp) -> None:
    temp_dir = node_temp.temp_dir_
    if not Path.exists(temp_dir):
        return
    for item in Path.iterdir(temp_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
