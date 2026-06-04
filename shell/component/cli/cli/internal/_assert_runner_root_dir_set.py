"""_assert_runner_root_dir_set.py
Responsible for one thing: raising ValueError when runner_root_dir is not set.
"""

from __future__ import annotations


def _assert_runner_root_dir_set(runner_root_dir: str | None) -> None:
    """Raise ValueError if runner_root_dir is None."""
    if runner_root_dir is None:
        raise ValueError("[Cli] runner_root_dir is not set — pass runner_root_dir=__file__ to init_app()")
