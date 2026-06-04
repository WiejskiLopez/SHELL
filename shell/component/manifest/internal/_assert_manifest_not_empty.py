"""_assert_manifest_not_empty.py
Responsible for one thing: raising ValueError when manifest.yaml content is empty.
"""


def _assert_manifest_not_empty(body: str, manifest_path) -> None:
    """Raise ValueError if manifest YAML body is blank."""
    if not body.strip():
        raise ValueError(f"[Manifest.load] manifest.yaml is empty: '{manifest_path}'")
