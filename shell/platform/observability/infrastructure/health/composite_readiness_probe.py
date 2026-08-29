"""CompositeReadinessProbe — combines several readiness probes into one report.

Every probe contributes its ``checks`` entries to a single report. The report is
ready only when every probe is ready, so a down broker or a flooded database
renders the service not ready even when the other checks pass.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.observability.application.ports.readiness import (
    ReadinessProbe,
    ReadinessReport,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class CompositeReadinessProbe(ReadinessProbe):
    def __init__(self, probes: Sequence[ReadinessProbe]) -> None:
        self._probes = tuple(probes)

    def __len__(self) -> int:
        return len(self._probes)

    async def check(self) -> ReadinessReport:
        checks: dict[str, object] = {}
        ready = True
        for probe in self._probes:
            report = await probe.check()
            ready = ready and report.ready
            checks.update(report.checks)
        return ReadinessReport(ready=ready, checks=checks)
