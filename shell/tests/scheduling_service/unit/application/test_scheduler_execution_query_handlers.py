"""Unit tests for SchedulerExecution query handlers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell.scheduling_service.application.scheduling.scheduler_execution.dto.scheduler_execution import (
    SchedulerExecutionDto,
)
from shell.scheduling_service.application.scheduling.scheduler_execution.queries.get_scheduler_execution_by_id_query import (
    GetSchedulerExecutionByIdQuery,
)
from shell.scheduling_service.application.scheduling.scheduler_execution.queries.list_scheduler_executions_query import (
    ListSchedulerExecutionsQuery,
)
from shell.scheduling_service.application.scheduling.scheduler_execution.query_handlers.get_scheduler_execution_by_id_handler import (
    GetSchedulerExecutionByIdHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_execution.query_handlers.list_scheduler_executions_handler import (
    ListSchedulerExecutionsHandler,
)

if TYPE_CHECKING:
    from shell.scheduling_service.application.scheduling.scheduler_execution.ports.scheduler_execution_query_service import (
        SchedulerExecutionQueryService,
    )


class FakeSchedulerExecutionQueryService:
    def __init__(
        self,
        by_id: SchedulerExecutionDto | None = None,
        all_rows: tuple[list[SchedulerExecutionDto], int] | None = None,
    ) -> None:
        self._by_id = by_id
        self._all = all_rows

    async def get_by_id(self, scheduler_execution_id: str) -> SchedulerExecutionDto | None:
        return self._by_id

    async def list_all(self) -> tuple[list[SchedulerExecutionDto], int] | None:
        return self._all


def _dto(execution_id: str = "exec-1") -> SchedulerExecutionDto:
    return SchedulerExecutionDto(
        id=execution_id,
        scheduler_definition_id="def-1",
        status="PENDING",
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )


class TestGetSchedulerExecutionByIdHandler:
    async def test_returns_dto_when_found(self) -> None:
        queries: SchedulerExecutionQueryService = FakeSchedulerExecutionQueryService(by_id=_dto())
        handler = GetSchedulerExecutionByIdHandler(queries)
        result = await handler.handle(GetSchedulerExecutionByIdQuery("exec-1"))
        assert result is not None
        assert result.id == "exec-1"
        assert result.status == "PENDING"

    async def test_returns_none_when_missing(self) -> None:
        queries: SchedulerExecutionQueryService = FakeSchedulerExecutionQueryService(by_id=None)
        handler = GetSchedulerExecutionByIdHandler(queries)
        result = await handler.handle(GetSchedulerExecutionByIdQuery("missing"))
        assert result is None


class TestListSchedulerExecutionsHandler:
    async def test_returns_list_and_total(self) -> None:
        queries: SchedulerExecutionQueryService = FakeSchedulerExecutionQueryService(
            all_rows=([_dto(), _dto("exec-2")], 2)
        )
        handler = ListSchedulerExecutionsHandler(queries)
        result = await handler.handle(ListSchedulerExecutionsQuery())
        assert result is not None
        dtos, total = result
        assert total == 2
        assert [d.id for d in dtos] == ["exec-1", "exec-2"]

    async def test_returns_empty_when_no_rows(self) -> None:
        queries: SchedulerExecutionQueryService = FakeSchedulerExecutionQueryService(
            all_rows=([], 0)
        )
        handler = ListSchedulerExecutionsHandler(queries)
        result = await handler.handle(ListSchedulerExecutionsQuery())
        assert result is not None
        assert result == ([], 0)
