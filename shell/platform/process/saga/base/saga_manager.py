"""SagaManager — abstrakcyjna maszyna stanów procesu (koordynator sag).

Podklasy per BC definiują: typy stanu (``state.py``), tabelę kroków
(``steps.py``) oraz metody ``on_*`` (guard → mutacja stanu → dispatch kolejnych
komend delivery). Saga nigdy nie implementuje logiki domenowej — wyłącznie
koordynację.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.platform.application.commands.command import Command
    from shell.platform.application.events.integration_event import IntegrationEvent
    from shell.platform.process.saga.ports.command_delivery_dispatcher import (
        CommandDeliveryDispatcher,
    )
    from shell.platform.process.saga.ports.saga_repository import SagaRepository
    from shell.platform.process.saga.ports.saga_timeout_repository import (
        SagaTimeoutRepository,
    )
    from shell.platform.process.saga.steps import StepDefinition, StepRegistry


class SagaManager(ABC):
    """Abstrakcyjny koordynator procesu; jedna instancja = jedna saga."""

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
    async def on_event(self, event: IntegrationEvent) -> None:
        """Guard na bieżącym stanie, mutacja stanu, dispatch następnych kroków."""
        raise NotImplementedError

    async def dispatch_step(self, step: StepDefinition, command: Command) -> str:
        """Wysyła komendę delivery kroku i rejestruje oczekiwany timeout.

        Dispatch nie wykonuje commitu — transakcję przetwarzania inboxu
        (stan sagi + outbox + ack) domyka procesor delivery.
        """
        command_id = await self._dispatch_to(step, command)
        if step.timeout is not None:
            await self._timeouts.schedule(
                saga_id=self._saga_id,
                saga_key=self._saga_key,
                step=step.name,
                due_in=step.timeout,
            )
        return command_id

    async def dispatch_compensation(self, step: StepDefinition, command: Command) -> str:
        """Wysyła komendę cofającą krok (bez rejestrowania timeoutu)."""
        return await self._dispatch_to(step, command)

    async def _dispatch_to(self, step: StepDefinition, command: Command) -> str:
        return await self._dispatcher.dispatch(
            command,
            target_service=step.target_service,
        )
