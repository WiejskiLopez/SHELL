from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    pass


class FakeEventPublisher:
    def __init__(self) -> None:
        self.published: list[object] = []

    async def publish(self, events: Sequence[object]) -> None:
        self.published.extend(events)
