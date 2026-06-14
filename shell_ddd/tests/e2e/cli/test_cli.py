"""E2E CLI tests — exercises the CLI main entry-point using an in-process call
(asyncio.run + ApplicationFactory with temp SQLite DB) to avoid subprocess overhead
while still validating the full stack: CLI → bus → handler → SQL → result."""
from __future__ import annotations

import os
import pathlib


def _db_url(tmp_path: pathlib.Path) -> str:
    return f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"


class TestCliImportTask:
    async def test_import_task_happy_path(self, tmp_path: pathlib.Path) -> None:
        md = tmp_path / "my_task.md"
        yaml_ = tmp_path / "my_task.yaml"
        md.write_text("# My Task", encoding="utf-8")
        yaml_.write_text("graph:\n  nodes: []\n", encoding="utf-8")

        os.environ["SHELL_DDD_DATABASE_URL"] = _db_url(tmp_path)
        try:
            from shell_ddd.framework.cli.main import _import_task
            rc = await _import_task([
                "--task-name", "my_task",
                "--task-dir", str(tmp_path),
            ])
        finally:
            del os.environ["SHELL_DDD_DATABASE_URL"]
        assert rc == 0

    async def test_import_task_missing_args_returns_1(self, tmp_path: pathlib.Path) -> None:
        os.environ["SHELL_DDD_DATABASE_URL"] = _db_url(tmp_path)
        try:
            from shell_ddd.framework.cli.main import _import_task
            rc = await _import_task([])
        finally:
            del os.environ["SHELL_DDD_DATABASE_URL"]
        assert rc == 1


class TestCliMain:
    def test_main_no_args_returns_1(self) -> None:
        from shell_ddd.framework.cli.main import main
        assert main([]) == 1

    def test_main_unknown_mode_returns_1(self) -> None:
        from shell_ddd.framework.cli.main import main
        assert main(["unknown_mode"]) == 1

    async def test_main_import_task_end_to_end(self, tmp_path: pathlib.Path) -> None:
        md = tmp_path / "e2e_task.md"
        yaml_ = tmp_path / "e2e_task.yaml"
        md.write_text("# E2E Task", encoding="utf-8")
        yaml_.write_text("graph:\n  nodes: []\n", encoding="utf-8")

        os.environ["SHELL_DDD_DATABASE_URL"] = _db_url(tmp_path)
        try:
            from shell_ddd.framework.cli.main import _import_task
            rc = await _import_task(["--task-name", "e2e_task", "--task-dir", str(tmp_path)])
        finally:
            del os.environ["SHELL_DDD_DATABASE_URL"]
        assert rc == 0


class TestCliParser:
    def test_parser_defaults(self) -> None:
        from shell_ddd.framework.cli.parser import parse_args
        ns = parse_args([])
        assert ns.mode is None
        assert ns.node_dir is None
        assert ns.dry_run is False
        assert ns.add_dirs == []

    def test_parser_flags(self) -> None:
        from shell_ddd.framework.cli.parser import parse_args
        ns = parse_args([
            "--node-dir", "/tmp/node",
            "--mode", "agent",
            "--model", "gpt-4o",
            "--max-step", "10",
            "--dry-run",
        ])
        assert ns.node_dir == "/tmp/node"
        assert ns.mode == "agent"
        assert ns.model == "gpt-4o"
        assert ns.max_step == 10
        assert ns.dry_run is True
