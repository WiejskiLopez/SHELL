"""_assert_node_name_resolvable.py
Responsible for one thing: raising ValueError when neither _node_name nor _node_dir is set.
"""


def _assert_node_name_resolvable(node_name: str | None, node_dir: str | None) -> None:
    """Raise ValueError if both node_name and node_dir are falsy."""
    if not node_name and not node_dir:
        raise ValueError("[Node] _node_name is not set and _node_dir is not set")
