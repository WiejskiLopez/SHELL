"""_assert_role_set.py
Responsible for one thing: raising ValueError when a graph node has no role defined.
"""


def _assert_role_set(role: str | None, node: dict) -> None:
    """Raise ValueError if role is falsy."""
    if not role:
        raise ValueError(f"[Router] node '{node.get('id', '?')}' has no role defined")
