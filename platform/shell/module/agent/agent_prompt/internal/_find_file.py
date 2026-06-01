
from shell.utils.path.path import Path, PathType


def _find_file(filename: str, node: PathType) -> PathType | None:
    for search_dir in [node / ".node" / "input", node / ".node" / "temp"]:
        if not Path.is_dir(search_dir):
            continue
        for match in Path.rglob(search_dir, filename):
            if Path.is_file(match):
                return match
    return None
