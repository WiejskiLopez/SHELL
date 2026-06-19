from __future__ import annotations

import os

from shell.tests.e2e.cli.conftest import _db_url


class TestCliMain:
    def test_main_no_args_returns_1(self) -> None:
        from shell.framework.platform.cli.main import main

        assert main([]) == 1

    def test_main_unknown_mode_returns_1(self) -> None:
        from shell.framework.platform.cli.main import main

        assert main(["unknown_mode"]) == 1

    async def test_main_import_task_execution_end_to_end(self, tmp_path) -> None:
        md = tmp_path / "e2e_task.md"
        md.write_text("# E2E Task", encoding="utf-8")

        os.environ["SHELL_DATABASE_URL"] = _db_url(tmp_path)
        try:
            from shell.framework.platform.cli.main import _import_task_execution

            rc = await _import_task_execution(
                ["--task-name", "e2e_task", "--task-dir", str(tmp_path)]
            )
        finally:
            del os.environ["SHELL_DATABASE_URL"]
        assert rc == 0
