from shell.utils.path.path import Path, PathType


def _assert_output_dir_exists(output_dir: PathType) -> None:
    if not Path.is_dir(output_dir):
        raise FileNotFoundError(f"Output directory does not exist: {output_dir}")
