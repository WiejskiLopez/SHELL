from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

from shell.domain.platform.events import (
    DomainEvent,  # noqa: TC002 — DomainEvent używany w typowaniu listy eventów
)
from shell.infrastructure.platform.logging.composite_event_publisher import CompositeEventPublisher
from shell.tests.conftest_helpers import _task_imported

if TYPE_CHECKING:
    from shell.application.platform.ports.ports import EventPublisher


class TestCompositeEventPublisher:
    async def test_fans_out_to_all_publishers(self) -> None:
        p1 = AsyncMock()
        p2 = AsyncMock()
        p3 = AsyncMock()
        composite = CompositeEventPublisher([p1, p2, p3])  # type: ignore[arg-type]
        events: list[DomainEvent] = [_task_imported()]
        await composite.publish(events)
        p1.publish.assert_awaited_once_with(events)
        p2.publish.assert_awaited_once_with(events)
        p3.publish.assert_awaited_once_with(events)

    async def test_preserves_order(self) -> None:
        order: list[int] = []

        async def make_mock(n: int) -> EventPublisher:
            class _Pub:
                async def publish(self, evs: list) -> None:
                    order.append(n)

            return _Pub()

        p1 = await make_mock(1)
        p2 = await make_mock(2)
        composite = CompositeEventPublisher([p1, p2])  # type: ignore[arg-type]
        await composite.publish([_task_imported()])
        assert order == [1, 2]

    async def test_empty_publisher_list(self) -> None:
        composite = CompositeEventPublisher([])
        await composite.publish([_task_imported()])
