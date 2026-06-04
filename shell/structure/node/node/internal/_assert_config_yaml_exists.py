from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_config_yaml_exists(path: PathType) -> None:
    if not Path.is_file(path):
        raise FileNotFoundError(f"[_validate_node] Node config not found: {path}")
