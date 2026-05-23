from shell.utils.path.path import PathType
from __future__ import annotations



def _assert_source_dir_set(source_dir: PathType | None) -> None:
    if source_dir is None:
        raise RuntimeError("[Node] source_dir is not set — pass --source-dir to the CLI")
