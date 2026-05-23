"""_assert_lock_path_set.py
Responsible for one thing: raising ValueError when _lock_path is not set.
"""


def _assert_lock_path_set(lock_path) -> None:
    """Raise ValueError if lock_path is falsy."""
    if not lock_path:
        raise ValueError("[Lock] _lock_path is not set")
