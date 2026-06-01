from __future__ import annotations

from shell.utils.path.path import PathType

from collections.abc import Callable

from shell.module.router.router.internal._parse_frontmatter import _parse_frontmatter

from shell.utils.io.io import default_read_utf8


def read_metadata_from_file(
    path: PathType,
    reader: Callable[[PathType], str] | None = None,
) -> dict:
    """Return parsed frontmatter metadata from file. Empty dict if none.

    reader: optional callable (path: PathType) -> str for testability.
    """
    if reader is None:
        reader = default_read_utf8
    text = reader(path)
    data, _ = _parse_frontmatter(text)
    return data or {}
