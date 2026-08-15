"""ReadinessProbe — real readiness beyond liveness.

``/health`` answers "is the process alive". ``/readiness`` answers "can this
process do useful work right now": database reachable, migrations applied,
worker making progress, backlog under a safe threshold.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ReadinessReport:
    ready: bool
    checks: dict[str, object] = field(default_factory=dict)


class ReadinessProbe(Protocol):
    async def check(self) -> ReadinessReport: ...
