"""SubprocessNodeProcessRunner — real NodeProcessRunner adapter using asyncio subprocess."""

from __future__ import annotations

import asyncio
import os
import pathlib
import sys
from typing import TYPE_CHECKING

from shell.domain.value_objects.execution_result import ExecutionResult

if TYPE_CHECKING:
    from shell.domain.value_objects.manifest import Manifest

# Modes that use the shell framework CLI entrypoint (not an external binary).
_FRAMEWORK_MODES = {"router", "tasker", "tool", "worker", "agent"}

# Path to shell/framework/entrypoints/ (resolved relative to this file).
_ENTRYPOINTS_DIR = pathlib.Path(__file__).parent.parent.parent / "framework" / "entrypoints"


class SubprocessNodeProcessRunner:
    """Runs a node subprocess using asyncio.create_subprocess_exec.

    Mode routing:
    - ``agent`` → ``copilot`` binary via ``build_agent_command``
    - ``router | tasker | tool | worker`` → Python + framework entrypoint via
      ``build_sub_node_command``
    """

    DEFAULT_TIMEOUT_SECONDS = 300

    async def run(
        self,
        manifest: Manifest,
        workspace_path: str,
        env: dict[str, str] | None = None,
    ) -> ExecutionResult:
        """Execute the node and return stdout/stderr/returncode."""
        mode = str(manifest.mode)
        run_env = {**os.environ, "PYTHONUTF8": "1"}
        if env:
            run_env.update(env)

        if mode == "agent":
            from shell.infrastructure.process.command_builder import build_agent_command

            argv = build_agent_command(
                manifest,
                workspace_path,
                model=getattr(manifest, "model", ""),
            )
        elif mode in _FRAMEWORK_MODES:
            argv = self._build_framework_argv(manifest, workspace_path, env or {})
        else:
            # Unknown mode — try executing manifest.name as a direct executable (fallback).
            argv = [manifest.name]

        return await self._run_argv(argv, workspace_path, run_env)

    # ------------------------------------------------------------------

    def _build_framework_argv(
        self,
        manifest: Manifest,
        workspace_path: str,
        env: dict[str, str],
    ) -> list[str]:
        """Return argv for running a sub-node via the framework entrypoint."""
        from shell.infrastructure.process.command_builder import build_sub_node_command

        mode = str(manifest.mode)
        entrypoint = str(_ENTRYPOINTS_DIR / f"{mode}_entrypoint.py")
        env.get("SHELL_WORKFLOW_ID", "")
        task_execution_id = env.get("SHELL_task_execution_id", "")

        return build_sub_node_command(
            entrypoint_path=entrypoint,
            node_dir=workspace_path,
            source_dir=workspace_path,
            work_dir=workspace_path,
            task_execution_id=task_execution_id,
            task_dir=workspace_path,
            mode=mode,
            role=manifest.role,
            python_exe=sys.executable,
        )

    async def _run_argv(
        self,
        argv: list[str],
        cwd: str,
        env: dict[str, str],
        stdin_data: str = "",
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> ExecutionResult:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            cwd=cwd,
            env=env,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdin_bytes = stdin_data.encode("utf-8") if stdin_data else None
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(input=stdin_bytes),
                timeout=timeout,
            )
        except TimeoutError:
            proc.kill()
            await proc.wait()
            return ExecutionResult(
                returncode=-1,
                stdout="",
                stderr=f"Process timed out after {timeout}s",
            )

        return ExecutionResult(
            returncode=proc.returncode if proc.returncode is not None else -1,
            stdout=stdout_bytes.decode("utf-8", errors="replace"),
            stderr=stderr_bytes.decode("utf-8", errors="replace"),
        )
