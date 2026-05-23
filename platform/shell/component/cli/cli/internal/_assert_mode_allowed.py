"""_assert_mode_allowed.py
Responsible for one thing: raising ValueError when mode is not one of the allowed CLI modes.
"""


def _assert_mode_allowed(mode: str) -> None:
    """Raise ValueError if mode is not 'agent' or 'tasker'."""
    if mode not in ('agent', 'tasker'):
        raise ValueError(f"[validate_args] mode is required: 'agent' | 'tasker', got: {mode!r}")
