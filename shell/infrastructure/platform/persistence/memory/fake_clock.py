from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


class FakeClock:
    def __init__(self, fixed: datetime) -> None:
        self._time = fixed

    def now(self) -> datetime:
        return self._time
