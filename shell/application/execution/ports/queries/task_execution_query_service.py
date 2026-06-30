from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.application.execution.dto.task_execution import TaskExecutionDto


class TaskExecutionQueryService(Protocol):
    """Port do bezpośredniego odczytu DTO zadań (omija domenę)."""

    async def get_task_execution_by_name(self, name: str) -> TaskExecutionDto | None: ...

    async def get_current_task(self, name: str) -> TaskExecutionDto | None: ...
