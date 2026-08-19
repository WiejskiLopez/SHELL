from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ReadinessReport:
    ready: bool
    checks: dict[str, object] = field(default_factory=dict)


class ReadinessProbe(Protocol):
    async def check(self) -> ReadinessReport: ...
