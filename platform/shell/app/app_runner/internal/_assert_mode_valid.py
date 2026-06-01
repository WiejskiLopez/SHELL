from __future__ import annotations


_MODES: frozenset[str] = frozenset({"agent", "tasker", "router", "tool", "worker"})


def _assert_mode_valid(mode: str | None) -> None:
    if mode is None:
        return
    if mode not in _MODES:
        raise ValueError(f"mode must be one of {sorted(_MODES)!r}, got {mode!r}")
