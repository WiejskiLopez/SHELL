"""_assert_node_name_set.py
Responsible for one thing: raising ValueError when _node_name is not set.
"""


def _assert_node_name_set(node_name: str | None) -> None:
    """Raise ValueError if node_name is falsy."""
    if not node_name:
        raise ValueError("[SubNode] _node_name is not set")
