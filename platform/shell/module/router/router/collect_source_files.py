
from shell.utils.path.path import Path, PathType


def collect_source_files(prev_output_dir: PathType) -> list[PathType]:
    if not Path.is_dir(prev_output_dir):
        return []
    return [f for f in Path.iterdir(prev_output_dir) if Path.is_file(f)]
