from __future__ import annotations

import os

from shell.tests.e2e.cli.conftest import _db_url


class TestCliImportTaskExecution:
    async def test_import_task_execution_happy_path(self, tmp_path) -> None:
        md = tmp_path / "my_task.md"
        md.write_text("# My Task", encoding="utf-8")

        os.environ["SHELL_DATABASE_URL"] = _db_url(tmp_path)
        try:
            from shell.framework.platform.cli.main import _import_task_execution

            rc = await _import_task_execution(
                [
                    "--task-name",
                    "my_task",
                    "--task-dir",
                    str(tmp_path),
                ]
            )
        finally:
            del os.environ["SHELL_DATABASE_URL"]
        assert rc == 0

    async def test_import_task_execution_missing_args_returns_1(
        self, tmp_path
    ) -> None:
        os.environ["SHELL_DATABASE_URL"] = _db_url(tmp_path)
        try:
            from shell.framework.platform.cli.main import _import_task_execution

            rc = await _import_task_execution([])
        finally:
            del os.environ["SHELL_DATABASE_URL"]
        assert rc == 1
