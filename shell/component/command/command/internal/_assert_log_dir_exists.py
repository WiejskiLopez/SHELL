from shell.utils.path.path import Path, PathType


def _assert_log_dir_exists(log_dir: PathType) -> None:
    if not Path.is_dir(log_dir):
        raise FileNotFoundError(f"Log directory does not exist: {log_dir}")
