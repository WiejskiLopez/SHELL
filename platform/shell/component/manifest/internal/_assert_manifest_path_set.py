"""_assert_manifest_path_set.py
Responsible for one thing: raising ValueError when _manifest_path is not set.
"""


def _assert_manifest_path_set(path) -> None:
    """Raise ValueError if manifest path is falsy."""
    if not path:
        raise ValueError("[Manifest] _manifest_path is not set")
