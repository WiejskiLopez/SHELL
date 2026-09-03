"""SagaRepository — port trwałości instancji sagi."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.platform.process.saga.saga_instance import SagaInstance


class SagaRepository(Protocol):
    """Trwałość instancji sagi konsumowana przez SagaManager."""

    async def get_by_key(self, saga_type: str, saga_key: str) -> SagaInstance | None: ...
    async def create(self, instance: SagaInstance) -> None: ...
    async def update(self, instance: SagaInstance) -> None: ...
