from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from shell.application.execution.commands.task_execution_commands import ImportTaskExecutionCommand
from shell.application.execution.queries.task_execution_queries import TaskExecutionGetByNameQuery
from shell.framework.execution.api.routers.task_executions.import_task_response import (
    ImportTaskResponse,
)

if TYPE_CHECKING:
    from shell.application.platform.bus.command_bus import CommandBus
    from shell.application.platform.bus.query_bus import QueryBus


class TaskExecutionController:
    __slots__ = ("_command_bus", "_query_bus")

    def __init__(self, command_bus: CommandBus, query_bus: QueryBus) -> None:
        self._command_bus = command_bus
        self._query_bus = query_bus

    async def import_task(self, md_path: str, task_execution_name: str) -> ImportTaskResponse:
        command = ImportTaskExecutionCommand(
            md_path=md_path, task_execution_name=task_execution_name
        )
        task_execution_id = await self._command_bus.dispatch(command)
        return ImportTaskResponse(task_execution_id=str(task_execution_id))

    async def get_task(self, name: str) -> dict:
        result = await self._query_bus.dispatch(TaskExecutionGetByNameQuery(name=name))
        if result is None:
            raise HTTPException(status_code=404, detail=f"Task '{name}' not found")
        return {"name": name, "task": str(result)}
