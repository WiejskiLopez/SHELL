from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.scheduling_service.application.scheduling.scheduler_definition.dto.scheduler_definition import (
        SchedulerDefinitionDto,
    )


class SchedulerDefinitionQueryService(Protocol):
    async def get_by_id(self, scheduler_definition_id: str) -> SchedulerDefinitionDto | None: ...
