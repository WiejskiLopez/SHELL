from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.exists_result import ExistsResult
    from shell.scheduling.domain.scheduling.aggregates.scheduler_job.scheduler_job import (
        SchedulerJob,
    )
    from shell.scheduling.domain.scheduling.aggregates.scheduler_job.value_objects.scheduler_job_id import (
        SchedulerJobId,
    )


class SchedulerJobRepository(Protocol):
    async def get_by_id(self, id: SchedulerJobId) -> SchedulerJob | None: ...

    async def save(self, job: SchedulerJob) -> None: ...

    async def delete(self, id: SchedulerJobId) -> None: ...

    async def exists(self, id: SchedulerJobId) -> ExistsResult: ...

    async def list_enabled(self) -> list[SchedulerJob]: ...

    async def list_all(self) -> list[SchedulerJob]: ...
