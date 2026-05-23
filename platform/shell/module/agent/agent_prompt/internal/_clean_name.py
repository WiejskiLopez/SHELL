"""_clean_name.py
Private. Responsible for one thing: turning a NNNN_snake_case stem into a
human-readable section heading (e.g. '0010_task_instructions' -> 'Task instructions').
"""

import re

_NUMERIC_PREFIX = re.compile(r"^\d+_")


def _clean_name(stem: str) -> str:
    """Strip leading digits+underscore, replace underscores with spaces, capitalize."""
    return _NUMERIC_PREFIX.sub("", stem).replace("_", " ").capitalize()
