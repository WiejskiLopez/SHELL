"""_assert_manifest_body_loaded.py
Responsible for one thing: raising ValueError when manifest_file_body is empty.
"""


def _assert_manifest_body_loaded(body: str) -> None:
    """Raise ValueError if manifest body is empty (init_manifest not called)."""
    if not body.strip():
        raise ValueError("[Manifest] manifest_file_body is empty — call init_manifest() first")
