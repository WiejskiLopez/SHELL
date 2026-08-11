from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.execution.application.execution.task_execution.dto.task_execution import (
        TaskExecutionDto,
    )


class TaskExecutionQueryService(Protocol):
    """Port do bezpośredniego odczytu DTO zadań (omija domenę)."""

    async def get_by_id(self, task_execution_id: str) -> TaskExecutionDto | None: ...

    async def get_task_execution_by_name(self, name: str) -> TaskExecutionDto | None: ...

    async def get_current_task(self, name: str) -> TaskExecutionDto | None: ...

    async def list_all(
        self, *, page: int = 1, page_size: int = 100
    ) -> tuple[list[TaskExecutionDto], int]: ...
