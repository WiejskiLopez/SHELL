"""_assert_file_body_not_empty.py
Validate that file_body is not empty.
"""

from __future__ import annotations


def _assert_file_body_not_empty(file_body: str) -> None:
    """Raise ValueError if file_body is empty."""
    if not file_body:
        raise ValueError("Cannot save empty file_body.")
