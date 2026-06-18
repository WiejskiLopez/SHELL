from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.value_objects.execution_result import ExecutionResult

if TYPE_CHECKING:
    from shell.domain.value_objects.manifest import Manifest


class FakeNodeProcessRunner:
    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0) -> None:
        self._stdout = stdout
        self._stderr = stderr
        self._returncode = returncode
        self.calls: list[dict[str, object]] = []

    async def run(
        self,
        manifest: Manifest,
        workspace_path: str,
        env: dict[str, str] | None = None,
    ) -> ExecutionResult:
        self.calls.append({"manifest": manifest, "workspace_path": workspace_path})
        return ExecutionResult(
            stdout=self._stdout,
            stderr=self._stderr,
            returncode=self._returncode,
        )
