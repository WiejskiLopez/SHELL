"""BrokerReadinessProbe for RabbitMQ — confirms broker reachability for readiness.

Opens a real broker connection with a bounded timeout and closes it again. A
successful round-trip proves the broker is reachable; any failure is reported as
an error string in ``checks`` instead of raising, so the /readiness endpoint can
answer 503 with a diagnostic body.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aio_pika import connect_robust

from shell.platform.observability.application.ports.readiness import (
    ReadinessProbe,
    ReadinessReport,
)

RabbitConnector = Callable[..., Awaitable[Any]]


class RabbitReadinessProbe(ReadinessProbe):
    def __init__(
        self,
        *,
        url_provider: Callable[[], str],
        connector: RabbitConnector | None = None,
        timeout: float = 5.0,
    ) -> None:
        self._url_provider = url_provider
        self._connector = connector or connect_robust
        self._timeout = timeout

    async def check(self) -> ReadinessReport:
        try:
            url = self._url_provider()
        except Exception as exc:
            return ReadinessReport(
                ready=False,
                checks={"broker": f"error: {type(exc).__name__}: {exc}"},
            )
        if not url:
            return ReadinessReport(
                ready=False,
                checks={"broker": "error: broker URL is not configured"},
            )
        try:
            connection = await self._connector(url, timeout=self._timeout)
        except Exception as exc:
            return ReadinessReport(
                ready=False,
                checks={"broker": f"error: {type(exc).__name__}: {exc}"},
            )
        try:
            await connection.close()
        except Exception as exc:
            return ReadinessReport(
                ready=False,
                checks={"broker": f"error: {type(exc).__name__}: {exc}"},
            )
        return ReadinessReport(ready=True, checks={"broker": True})
