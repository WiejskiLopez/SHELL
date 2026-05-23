from shell.utils.path.path import PathType
"""_assert_suffix_allowed.py
Validate that a file suffix is in the allowed set.
"""

from __future__ import annotations


_ALLOWED_SUFFIXES: frozenset[str] = frozenset({
    ".md", ".txt", ".yaml", ".yml", ".json", ".log",
})


def _assert_suffix_allowed(file_path: PathType) -> None:
    """Raise ValueError if file_path suffix is not in _ALLOWED_SUFFIXES."""
    if file_path.suffix.lower() not in _ALLOWED_SUFFIXES:
        raise ValueError(
            f"Unsupported file type: '{file_path.suffix}'. "
            f"Allowed: {sorted(_ALLOWED_SUFFIXES)}"
        )
