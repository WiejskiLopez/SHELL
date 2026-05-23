"""_resolve_level.py
Private. Responsible for one thing: converting a log-level name string
(e.g. 'DEBUG', 'info') to the corresponding logging integer constant.
"""

import logging


def _resolve_level(level_name: str) -> int:
    """Return the logging int for level_name; defaults to INFO for unknown values."""
    return getattr(logging, str(level_name).strip().upper(), logging.INFO)
