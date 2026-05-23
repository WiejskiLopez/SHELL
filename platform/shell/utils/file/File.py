"""File.py
File — DOM node representing a single file on disk.

Fields:
    _file_path  — absolute path to the file
    _file_body  — cached file content (str)

Properties:
    file_body_  — validated file content, raises ValueError if not loaded
"""

from __future__ import annotations

from shell.utils.path.path import Path, PathType

from shell.utils.file.internal._assert_file_loaded import _assert_file_loaded
from shell.utils.file.internal._read_file import _read_file
from shell.utils.file.internal._save_file import _save_file


class File:
    """DOM node for a single file on disk."""

    __slots__ = ("_file_path", "_file_body")

    def __init__(self, path: str | PathType) -> None:
        self._file_path: PathType = Path.new(path)
        self._file_body: str = ""

    @property
    def file_body_(self) -> str:
        """Return file content. Raises ValueError if not yet loaded."""
        _assert_file_loaded(self._file_body, self._file_path)
        return self._file_body

    def read_file(self, encoding: str = "utf-8") -> None:
        """Read file from disk into _file_body.

        Raises ValueError for unsupported file types.
        Raises OSError if file cannot be read.
        """
        self._file_body = _read_file(self._file_path, encoding)

    def save_file(self, encoding: str = "utf-8") -> None:
        """Write _file_body to disk.

        Raises ValueError if file_body is empty or file type is unsupported.
        """
        _save_file(self._file_path, self._file_body, encoding)
