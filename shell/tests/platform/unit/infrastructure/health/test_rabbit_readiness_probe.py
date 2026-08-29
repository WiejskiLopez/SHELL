"""Unit tests — RabbitReadinessProbe broker reachability checks."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aio_pika import connect_robust

from shell.platform.observability.infrastructure.health.rabbit_readiness_probe import (
    RabbitReadinessProbe,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from shell.platform.observability.application.ports.readiness import ReadinessReport


def _broker_check(report: ReadinessReport) -> str:
    value = report.checks["broker"]
    assert isinstance(value, str)
    return value


class _FakeConnection:
    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True


class _CloseFailingConnection(_FakeConnection):
    async def close(self) -> None:
        raise RuntimeError("close failed")


class _RecordingConnector:
    def __init__(self, connection: _FakeConnection | None = None) -> None:
        self.calls: list[tuple[str, float]] = []
        self._connection = connection or _FakeConnection()

    async def __call__(self, url: str, *, timeout: float) -> _FakeConnection:
        self.calls.append((url, timeout))
        return self._connection


async def _failing_connector(url: str, *, timeout: float) -> _FakeConnection:
    raise ConnectionError("broker unreachable")


def _url_provider(url: str = "amqp://shell:shell@localhost:5672") -> Callable[[], str]:
    return lambda: url


def _probe(
    connector: _RecordingConnector,
    url: str = "amqp://shell:shell@localhost:5672",
) -> RabbitReadinessProbe:
    return RabbitReadinessProbe(
        url_provider=_url_provider(url),
        connector=connector,
        timeout=2.0,
    )


class TestRabbitReadinessProbe:
    async def test_ready_when_broker_reachable(self) -> None:
        connector = _RecordingConnector()
        probe = _probe(connector)
        report = await probe.check()

        assert report.ready is True
        assert report.checks["broker"] is True
        assert connector._connection.closed is True

    async def test_timeout_and_url_forwarded_to_connector(self) -> None:
        connector = _RecordingConnector()
        probe = _probe(connector, url="amqp://probe:probe@rabbit:5672")
        await probe.check()

        assert connector.calls == [("amqp://probe:probe@rabbit:5672", 2.0)]

    async def test_connect_failure_is_not_ready(self) -> None:
        probe = RabbitReadinessProbe(
            url_provider=_url_provider(),
            connector=_failing_connector,
        )
        report = await probe.check()

        assert report.ready is False
        assert "error:" in _broker_check(report)

    async def test_close_failure_is_not_ready(self) -> None:
        connector = _RecordingConnector(_CloseFailingConnection())
        probe = _probe(connector)
        report = await probe.check()

        assert report.ready is False
        assert "error:" in _broker_check(report)

    async def test_empty_url_is_not_ready(self) -> None:
        connector = _RecordingConnector()
        probe = _probe(connector, url="")
        report = await probe.check()

        assert report.ready is False
        assert report.checks["broker"] == "error: broker URL is not configured"

    async def test_url_provider_failure_is_not_ready(self) -> None:
        def raising_provider() -> str:
            raise RuntimeError("config not set")

        probe = RabbitReadinessProbe(
            url_provider=raising_provider,
            connector=_RecordingConnector(),
        )
        report = await probe.check()

        assert report.ready is False
        assert "error:" in _broker_check(report)

    def test_defaults_to_aio_pika_connect_robust(self) -> None:
        probe = RabbitReadinessProbe(url_provider=_url_provider())

        assert probe._connector is connect_robust
