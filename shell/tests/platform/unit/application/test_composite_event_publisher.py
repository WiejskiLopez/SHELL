from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

from shell.platform.infrastructure.logging.composite_event_publisher import CompositeEventPublisher
from shell.tests.shared.sample_aggregate import make_sample_event

if TYPE_CHECKING:
    from collections.abc import Sequence

    from shell.platform.application.ports.ports import EventPublisher


class TestCompositeEventPublisher:
    async def test_fans_out_to_all_publishers(self) -> None:
        p1 = AsyncMock()
        p2 = AsyncMock()
        p3 = AsyncMock()
        composite = CompositeEventPublisher([p1, p2, p3])
        events: list[object] = [make_sample_event()]
        await composite.publish(events)
        p1.publish.assert_awaited_once_with(events)
        p2.publish.assert_awaited_once_with(events)
        p3.publish.assert_awaited_once_with(events)

    async def test_preserves_order(self) -> None:
        order: list[int] = []

        async def make_mock(n: int) -> EventPublisher:
            class _Pub:
                async def publish(self, evs: Sequence[object]) -> None:
                    order.append(n)

            return _Pub()

        p1 = await make_mock(1)
        p2 = await make_mock(2)
        composite = CompositeEventPublisher([p1, p2])
        await composite.publish([make_sample_event()])
        assert order == [1, 2]

    async def test_empty_publisher_list(self) -> None:
        composite = CompositeEventPublisher([])
        await composite.publish([make_sample_event()])
