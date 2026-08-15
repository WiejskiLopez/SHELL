from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from shell.platform.application.ports.unit_of_work import UnitOfWork
from shell.scheduling.domain.scheduling.aggregates.scheduler_definition.repositories.scheduler_definition_repository import (
    SchedulerDefinitionRepository,
)
from shell.scheduling.domain.scheduling.aggregates.scheduler_execution.repositories.scheduler_execution_repository import (
    SchedulerExecutionRepository,
)
from shell.scheduling.domain.scheduling.aggregates.scheduler_job.repositories.scheduler_job_repository import (
    SchedulerJobRepository,
)
from shell.scheduling.infrastructure.scheduling.scheduler_definition.persistence.memory.in_memory_scheduler_definition_repository import (
    InMemorySchedulerDefinitionRepository,
)
from shell.scheduling.infrastructure.scheduling.scheduler_execution.persistence.memory.in_memory_scheduler_execution_repository import (
    InMemorySchedulerExecutionRepository,
)
from shell.scheduling.infrastructure.scheduling.scheduler_job.persistence.memory.in_memory_scheduler_job_repository import (
    InMemorySchedulerJobRepository,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from shell.platform.domain.events import DomainEvent

TRepository = TypeVar("TRepository")


class InMemorySchedulingUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self._scheduler_definition_repository = InMemorySchedulerDefinitionRepository()
        self._scheduler_execution_repository = InMemorySchedulerExecutionRepository()
        self._scheduler_job_repository = InMemorySchedulerJobRepository()

        self._committed = False
        self._staged_events: list[DomainEvent] = []
        self._staged_messages: list[object] = []
        self._committed_events: list[DomainEvent] = []

    def repository(self, repo_type: type[TRepository]) -> TRepository:
        repos: dict[type, object] = {
            InMemorySchedulerDefinitionRepository: self._scheduler_definition_repository,
            SchedulerDefinitionRepository: self._scheduler_definition_repository,
            InMemorySchedulerExecutionRepository: self._scheduler_execution_repository,
            SchedulerExecutionRepository: self._scheduler_execution_repository,
            InMemorySchedulerJobRepository: self._scheduler_job_repository,
            SchedulerJobRepository: self._scheduler_job_repository,
        }
        repo = repos.get(repo_type)
        if repo is None:
            msg = f"Unknown repository type: {repo_type}"
            raise ValueError(msg)
        return repo  # type: ignore[return-value]

    def stage_events(self, events: Sequence[object]) -> None:
        self._staged_events.extend(events)  # type: ignore[arg-type]

    async def save(self, repo_type: type, aggregate: object) -> None:
        repo: Any = self.repository(repo_type)
        await repo.save(aggregate)
        self.stage_events(aggregate.pull_events())  # type: ignore[attr-defined]

    def stage_messages(self, messages: list[object]) -> None:
        self._staged_messages.extend(messages)

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._staged_events)

    @property
    def committed_events(self) -> list[DomainEvent]:
        return list(self._committed_events)

    async def __aenter__(self) -> InMemorySchedulingUnitOfWork:
        self._committed = False
        self._staged_events = []
        self._staged_messages = []
        self._committed_events = []
        return self

    async def __aexit__(self, *args: object) -> None:
        if args[0] is None:
            await self.commit()
        else:
            await self.rollback()

    async def commit(self) -> None:
        self._committed = True
        self._committed_events.extend(self._staged_events)
        self._staged_events.clear()
        self._staged_messages.clear()

    async def rollback(self) -> None:
        self._staged_events.clear()
