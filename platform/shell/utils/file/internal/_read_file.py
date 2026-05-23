from __future__ import annotations


from shell.utils.file.internal._assert_suffix_allowed import _assert_suffix_allowed
from shell.utils.path.path import Path, PathType


def _read_file(file_path: PathType, encoding: str = "utf-8") -> str:
    _assert_suffix_allowed(file_path)
    return Path.read_text(file_path)
