from __future__ import annotations

from datetime import timedelta

import pytest
from saga_orchestration.infrastructure.process.saga.in_memory_saga_repository import (
    InMemorySagaRepository,
)
from saga_orchestration.process.saga import SagaManager, StepDefinition, StepRegistry


class Dispatcher:
    def __init__(self) -> None:
        self.commands: list[tuple[object, str]] = []

    async def dispatch(self, command: object, *, target_service: str) -> str:
        self.commands.append((command, target_service))
        return "command-1"


class Timeouts:
    def __init__(self) -> None:
        self.scheduled: list[tuple[str, str, str, timedelta]] = []

    async def schedule(self, *, saga_id: str, saga_key: str, step: str, due_in: timedelta) -> None:
        self.scheduled.append((saga_id, saga_key, step, due_in))

    async def cancel(self, *, saga_id: str, step: str) -> None:
        return None


class SampleSaga(SagaManager):
    async def on_event(self, event: object) -> None:
        return None


@pytest.mark.asyncio
async def test_dispatch_step_uses_key_and_schedules_timeout() -> None:
    dispatcher = Dispatcher()
    timeouts = Timeouts()
    manager = SampleSaga(
        saga_id="saga-1",
        saga_key="order-1",
        steps=StepRegistry(steps=()),
        dispatcher=dispatcher,
        repository=InMemorySagaRepository(),
        timeouts=timeouts,
    )
    step = StepDefinition(name="charge", target_service="payments", timeout=timedelta(seconds=5))

    result = await manager.dispatch_step(step, object())

    assert result == "command-1"
    assert dispatcher.commands[0][1] == "payments"
    assert timeouts.scheduled == [("saga-1", "order-1", "charge", timedelta(seconds=5))]


@pytest.mark.asyncio
async def test_in_memory_repository_enforces_type_and_key_uniqueness() -> None:
    repository = InMemorySagaRepository()
    instance = make_saga_instance("saga-1", "order_fulfillment", "order-1")

    await repository.create(instance)

    with pytest.raises(ValueError, match="already exists"):
        await repository.create(instance)


def make_saga_instance(saga_id: str, saga_type: str, saga_key: str):
    from saga_orchestration.process.saga import SagaInstance, SagaStatus

    return SagaInstance(
        saga_id=saga_id,
        saga_type=saga_type,
        saga_key=saga_key,
        status=SagaStatus.RUNNING,
    )
