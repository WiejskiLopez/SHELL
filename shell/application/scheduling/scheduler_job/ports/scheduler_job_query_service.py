from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.application.scheduling.scheduler_job.dto.scheduler_job import SchedulerJobDto


class SchedulerJobQueryService(Protocol):
    async def get_by_id(self, scheduler_job_id: str) -> SchedulerJobDto | None: ...

    async def list_all(self) -> tuple[list[SchedulerJobDto], int] | None: ...

    async def list_enabled(self) -> list[SchedulerJobDto]: ...
