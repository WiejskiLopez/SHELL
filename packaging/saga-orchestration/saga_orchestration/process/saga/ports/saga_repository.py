from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from saga_orchestration.process.saga.saga_instance import SagaInstance


class SagaRepository(Protocol):
    async def get_by_key(self, saga_type: str, saga_key: str) -> SagaInstance | None: ...
    async def create(self, instance: SagaInstance) -> None: ...
    async def update(self, instance: SagaInstance) -> None: ...
