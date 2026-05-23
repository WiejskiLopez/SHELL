from __future__ import annotations

from shell.utils.path.path import PathType


def _assert_output_files_found(output_files: list, output_dir: PathType) -> None:
    if not output_files:
        raise FileNotFoundError(f"[NodeOutput] no file found in output_dir: {output_dir}")
