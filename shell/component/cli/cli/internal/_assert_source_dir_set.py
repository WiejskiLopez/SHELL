from __future__ import annotations


def _assert_source_dir_set(source_dir: str | None, mode: str | None) -> None:
    if mode == 'tasker' and source_dir is None:
        raise ValueError("[Cli] --source-dir is required in tasker mode")
