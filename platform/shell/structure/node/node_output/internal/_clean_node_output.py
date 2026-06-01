from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _clean_node_output(node_output) -> None:
    output_dir = node_output.output_dir_
    if not Path.exists(output_dir):
        return
    for item in Path.iterdir(output_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
