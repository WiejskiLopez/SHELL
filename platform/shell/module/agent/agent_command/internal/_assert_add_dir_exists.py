
from shell.utils.path.path import Path, PathType


def _assert_add_dir_exists(add_dir: PathType) -> None:
    if not Path.is_dir(add_dir):
        raise FileNotFoundError(f"Add directory does not exist: {add_dir}")
