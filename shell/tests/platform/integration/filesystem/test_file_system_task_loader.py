from __future__ import annotations

import pathlib

from shell.execution_service.infrastructure.execution.task_execution.filesystem.task_execution_loader import (
    FileSystemTaskLoader,
)


class TestFileSystemTaskLoader:
    async def test_load_reads_both_files(self, tmp_path: object) -> None:
        md = pathlib.Path(str(tmp_path)) / "task_execution.md"
        md.write_text("# My Task", encoding="utf-8")
        loader = FileSystemTaskLoader()
        task_text = await loader.load(str(md))
        assert task_text == "# My Task"
