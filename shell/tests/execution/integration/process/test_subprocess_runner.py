"""Integration tests for SubprocessGraphNodeExecutionProcessRunner."""

from __future__ import annotations

import sys

from shell.domain.execution.value_objects.manifest import Manifest
from shell.domain.platform.value_objects.mode import Mode
from shell.infrastructure.execution.process.subprocess_runner import (
    SubprocessGraphNodeExecutionProcessRunner,
)


def _make_manifest(name: str, mode: Mode = Mode.WORKER) -> Manifest:
    return Manifest(name=name, mode=mode, role=str(mode), node_type="node", version="0")


class TestSubprocessGraphNodeExecutionProcessRunner:
    async def test_echo_stdout(self, tmp_path: object) -> None:
        runner = SubprocessGraphNodeExecutionProcessRunner()
        # Use python -c "print('ok')" so tests work on Windows and Linux
        _make_manifest(name=sys.executable, mode=Mode.WORKER)
        result = await runner._run_argv(
            [sys.executable, "-c", "print('ok')"],
            cwd=str(tmp_path),
            env={},
        )
        assert result.returncode == 0
        assert "ok" in result.stdout

    async def test_stderr_captured(self, tmp_path: object) -> None:
        runner = SubprocessGraphNodeExecutionProcessRunner()
        result = await runner._run_argv(
            [sys.executable, "-c", "import sys; sys.stderr.write('err')"],
            cwd=str(tmp_path),
            env={},
        )
        assert result.returncode == 0
        assert "err" in result.stderr

    async def test_nonzero_returncode(self, tmp_path: object) -> None:
        runner = SubprocessGraphNodeExecutionProcessRunner()
        result = await runner._run_argv(
            [sys.executable, "-c", "raise SystemExit(42)"],
            cwd=str(tmp_path),
            env={},
        )
        assert result.returncode == 42

    async def test_timeout_returns_negative_one(self, tmp_path: object) -> None:
        runner = SubprocessGraphNodeExecutionProcessRunner()
        result = await runner._run_argv(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            cwd=str(tmp_path),
            env={},
            timeout=0.2,
        )
        assert result.returncode == -1
        assert "timed out" in result.stderr.lower()
