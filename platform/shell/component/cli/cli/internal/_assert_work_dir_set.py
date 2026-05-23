from __future__ import annotations


def _assert_work_dir_set(work_dir: str | None) -> None:
    if work_dir is None:
        raise ValueError("[Cli] --work-dir is required")
