from __future__ import annotations


from shell.utils.file.internal._assert_file_body_not_empty import _assert_file_body_not_empty
from shell.utils.file.internal._assert_suffix_allowed import _assert_suffix_allowed
from shell.utils.path.path import Path, PathType


def _save_file(file_path: PathType, file_body: str, encoding: str = "utf-8") -> None:
    _assert_file_body_not_empty(file_body)
    _assert_suffix_allowed(file_path)
    Path.mkdir(file_path.parent)
    Path.write_text(file_path, file_body)
