from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution.application.execution.task_execution.queries.list_task_executions_query import (
    ListTaskExecutionsQuery,
)
from shell.execution.framework.execution.task_execution.api.task_execution_response import (
    TaskExecutionResponse as ApiTaskExecutionResponse,
)
from shell.platform.framework.api.models.page import Page

if TYPE_CHECKING:
    from shell.execution.application.execution.task_execution.dto.task_execution import (
        TaskExecutionDto,
    )
    from shell.platform.application.bus.query_bus import QueryBus


def _dto_to_response(dto: TaskExecutionDto) -> ApiTaskExecutionResponse:
    return ApiTaskExecutionResponse(
        id=dto.id,
        name=dto.name,
        work_dir=dto.work_dir,
        workflow_id=dto.workflow_id,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
        deleted_at=dto.deleted_at,
    )


class TaskExecutionController:
    __slots__ = ("_query_bus",)

    def __init__(self, query_bus: QueryBus) -> None:
        self._query_bus = query_bus

    async def list_task_executions(
        self, page: int = 1, page_size: int = 100
    ) -> Page[ApiTaskExecutionResponse]:
        dtos, total = await self._query_bus.dispatch(
            ListTaskExecutionsQuery(page=page, page_size=page_size)
        )
        items = [_dto_to_response(d) for d in dtos]
        has_more = (page * page_size) < total
        return Page(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )
