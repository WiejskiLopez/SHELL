"""Unit tests for SchedulerJob query handlers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell.scheduling_service.application.scheduling.scheduler_job.dto.scheduler_job import (
    SchedulerJobDto,
)
from shell.scheduling_service.application.scheduling.scheduler_job.queries.get_scheduler_job_by_id_query import (
    GetSchedulerJobByIdQuery,
)
from shell.scheduling_service.application.scheduling.scheduler_job.queries.list_scheduler_jobs_query import (
    ListSchedulerJobsQuery,
)
from shell.scheduling_service.application.scheduling.scheduler_job.query_handlers.get_scheduler_job_by_id_handler import (
    GetSchedulerJobByIdHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_job.query_handlers.list_scheduler_jobs_handler import (
    ListSchedulerJobsHandler,
)

if TYPE_CHECKING:
    from shell.scheduling_service.application.scheduling.scheduler_job.ports.scheduler_job_query_service import (
        SchedulerJobQueryService,
    )


class FakeSchedulerJobQueryService:
    def __init__(
        self,
        by_id: SchedulerJobDto | None = None,
        all_rows: tuple[list[SchedulerJobDto], int] | None = None,
    ) -> None:
        self._by_id = by_id
        self._all = all_rows

    async def get_by_id(self, scheduler_job_id: str) -> SchedulerJobDto | None:
        return self._by_id

    async def list_all(self) -> tuple[list[SchedulerJobDto], int] | None:
        return self._all


def _dto(job_id: str = "job-1") -> SchedulerJobDto:
    return SchedulerJobDto(
        id=job_id,
        scheduler_definition_id="def-1",
        name="test-job",
        job_type="messaging",
        interval_seconds=5.0,
        batch_size=10,
        enabled=True,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )


class TestGetSchedulerJobByIdHandler:
    async def test_returns_dto_when_found(self) -> None:
        queries: SchedulerJobQueryService = FakeSchedulerJobQueryService(by_id=_dto())
        handler = GetSchedulerJobByIdHandler(queries)
        result = await handler.handle(GetSchedulerJobByIdQuery("job-1"))
        assert result is not None
        assert result.id == "job-1"
        assert result.name == "test-job"

    async def test_returns_none_when_missing(self) -> None:
        queries: SchedulerJobQueryService = FakeSchedulerJobQueryService(by_id=None)
        handler = GetSchedulerJobByIdHandler(queries)
        result = await handler.handle(GetSchedulerJobByIdQuery("missing"))
        assert result is None


class TestListSchedulerJobsHandler:
    async def test_returns_list_and_total(self) -> None:
        queries: SchedulerJobQueryService = FakeSchedulerJobQueryService(
            all_rows=([_dto(), _dto("job-2")], 2)
        )
        handler = ListSchedulerJobsHandler(queries)
        result = await handler.handle(ListSchedulerJobsQuery())
        assert result is not None
        dtos, total = result
        assert total == 2
        assert [d.id for d in dtos] == ["job-1", "job-2"]

    async def test_returns_empty_when_no_rows(self) -> None:
        queries: SchedulerJobQueryService = FakeSchedulerJobQueryService(all_rows=([], 0))
        handler = ListSchedulerJobsHandler(queries)
        result = await handler.handle(ListSchedulerJobsQuery())
        assert result is not None
        assert result == ([], 0)
