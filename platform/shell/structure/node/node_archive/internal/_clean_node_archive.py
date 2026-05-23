from __future__ import annotations

from shell.utils.path.path import Path


def _clean_node_archive(node_archive) -> None:
    node_archive_dir = node_archive.node_archive_dir_
    if not Path.exists(node_archive_dir):
        return
    for item in Path.iterdir(node_archive_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
