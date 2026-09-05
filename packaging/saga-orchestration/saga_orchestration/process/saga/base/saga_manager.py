from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from saga_orchestration.process.saga.ports.command_delivery_dispatcher import (
        CommandDeliveryDispatcher,
    )
    from saga_orchestration.process.saga.ports.saga_repository import SagaRepository
    from saga_orchestration.process.saga.ports.saga_timeout_repository import (
        SagaTimeoutRepository,
    )
    from saga_orchestration.process.saga.steps import StepDefinition, StepRegistry


class SagaManager(ABC):
    __slots__ = (
        "_saga_id",
        "_saga_key",
        "_steps",
        "_dispatcher",
        "_repository",
        "_timeouts",
    )

    def __init__(
        self,
        saga_id: str,
        saga_key: str,
        steps: StepRegistry,
        dispatcher: CommandDeliveryDispatcher,
        repository: SagaRepository,
        timeouts: SagaTimeoutRepository,
    ) -> None:
        self._saga_id = saga_id
        self._saga_key = saga_key
        self._steps = steps
        self._dispatcher = dispatcher
        self._repository = repository
        self._timeouts = timeouts

    @property
    def saga_id(self) -> str:
        return self._saga_id

    @property
    def saga_key(self) -> str:
        return self._saga_key

    @abstractmethod
    async def on_event(self, event: object) -> None:
        raise NotImplementedError

    async def dispatch_step(self, step: StepDefinition, command: object) -> str:
        command_id = await self._dispatcher.dispatch(
            command,
            target_service=step.target_service,
        )
        if step.timeout is not None:
            await self._timeouts.schedule(
                saga_id=self._saga_id,
                saga_key=self._saga_key,
                step=step.name,
                due_in=step.timeout,
            )
        return command_id

    async def dispatch_compensation(self, step: StepDefinition, command: object) -> str:
        return await self._dispatcher.dispatch(
            command,
            target_service=step.target_service,
        )
