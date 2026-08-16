from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from shell.platform.application.ports.unit_of_work import UnitOfWork
from shell.platform.infrastructure.mapping.reflective_integration_mapper import (
    ReflectiveIntegrationMapper,
)
from shell.session_service.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)
from shell.session_service.domain.session.aggregates.session_state.repositories.session_state_repository import (
    SessionStateRepository,
)
from shell.session_service.infrastructure.session.session.persistence.memory.in_memory_session_repository import (
    InMemorySessionRepository,
)
from shell.session_service.infrastructure.session.session_state.persistence.memory.in_memory_session_state_repository import (
    InMemorySessionStateRepository,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from shell.platform.domain.events import DomainEvent

TRepository = TypeVar("TRepository")


class InMemorySessionUnitOfWork(UnitOfWork):
    def __init__(self, mapper: Any | None = None) -> None:
        self._session_repository = InMemorySessionRepository()
        self._session_state_repository = InMemorySessionStateRepository()
        self._mapper = mapper or ReflectiveIntegrationMapper()

        self._committed = False
        self._staged_events: list[DomainEvent] = []
        self._staged_messages: list[object] = []
        self._committed_events: list[DomainEvent] = []

    def repository(self, repo_type: type[TRepository]) -> TRepository:
        repos: dict[type, object] = {
            InMemorySessionRepository: self._session_repository,
            SessionRepository: self._session_repository,
            InMemorySessionStateRepository: self._session_state_repository,
            SessionStateRepository: self._session_state_repository,
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
        domain_events = aggregate.pull_events()  # type: ignore[attr-defined]
        mapped = [self._mapper.map(event) for event in domain_events]
        self.stage_events(mapped)

    def stage_messages(self, messages: list[object]) -> None:
        self._staged_messages.extend(messages)

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._staged_events)

    @property
    def committed_events(self) -> list[DomainEvent]:
        return list(self._committed_events)

    async def __aenter__(self) -> InMemorySessionUnitOfWork:
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
