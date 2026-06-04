from __future__ import annotations

from shell.utils.path.path import Path


def _clean_node_scripts(node_scripts) -> None:
    scripts_dir = node_scripts.scripts_dir_
    if not Path.exists(scripts_dir):
        return
    for item in Path.iterdir(scripts_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
