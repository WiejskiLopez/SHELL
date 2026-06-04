"""_assert_mode_valid.py
Responsible for one thing: raising ValueError when mode is not in the allowed set.
"""


def _assert_mode_valid(mode: str, modes: frozenset) -> None:
    """Raise ValueError if mode is not in the allowed modes set."""
    if mode not in modes:
        raise ValueError(f"[set_mode] mode must be one of {sorted(modes)}, got: {mode!r}")
