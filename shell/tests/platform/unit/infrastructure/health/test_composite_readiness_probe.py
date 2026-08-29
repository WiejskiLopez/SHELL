"""Unit tests — CompositeReadinessProbe report merging."""

from __future__ import annotations

from shell.platform.observability.application.ports.readiness import (
    ReadinessProbe,
    ReadinessReport,
)
from shell.platform.observability.infrastructure.health.composite_readiness_probe import (
    CompositeReadinessProbe,
)


class _StubProbe(ReadinessProbe):
    def __init__(self, ready: bool, checks: dict[str, object]) -> None:
        self._ready = ready
        self._checks = checks

    async def check(self) -> ReadinessReport:
        return ReadinessReport(ready=self._ready, checks=self._checks)


def _ready_probe(name: str) -> _StubProbe:
    return _StubProbe(True, {name: True})


def _failed_probe(name: str) -> _StubProbe:
    return _StubProbe(False, {name: "error: down"})


class TestCompositeReadinessProbe:
    async def test_ready_when_all_probes_ready(self) -> None:
        composite = CompositeReadinessProbe([_ready_probe("database"), _ready_probe("broker")])
        report = await composite.check()

        assert report.ready is True
        assert report.checks == {"database": True, "broker": True}

    async def test_not_ready_when_any_probe_fails(self) -> None:
        composite = CompositeReadinessProbe([_ready_probe("database"), _failed_probe("broker")])
        report = await composite.check()

        assert report.ready is False
        assert report.checks["database"] is True
        assert report.checks["broker"] == "error: down"

    async def test_checks_are_merged_flat(self) -> None:
        composite = CompositeReadinessProbe(
            [_ready_probe("database"), _ready_probe("worker"), _ready_probe("broker")]
        )
        report = await composite.check()

        assert list(report.checks) == ["database", "worker", "broker"]

    async def test_len_counts_probes(self) -> None:
        composite = CompositeReadinessProbe([_ready_probe("database"), _ready_probe("broker")])

        assert len(composite) == 2
