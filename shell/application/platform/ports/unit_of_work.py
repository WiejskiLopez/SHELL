from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar

if TYPE_CHECKING:
    from shell.domain.platform.aggregates.message.message import Message
    from shell.domain.platform.events import DomainEvent

TRepository = TypeVar("TRepository")


class UnitOfWork(Protocol):
    def repository(self, repo_type: type[TRepository]) -> TRepository: ...

    def stage_events(self, events: list[DomainEvent]) -> None: ...

    def stage_messages(self, messages: list[Message]) -> None: ...

    @property
    def events(self) -> list[DomainEvent]: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...

    async def __aenter__(self) -> UnitOfWork: ...

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None: ...
