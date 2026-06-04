"""_assert_file_loaded.py
Validate that file has been loaded (file_body is not empty).
"""

from __future__ import annotations

from shell.utils.path.path import PathType




def _assert_file_loaded(file_body: str, file_path: PathType) -> None:
    """Raise ValueError if file_body is empty (file not yet loaded)."""
    if not file_body:
        raise ValueError(f"File not loaded: {file_path}")
