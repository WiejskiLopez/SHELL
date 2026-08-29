"""MetricsMiddleware — records inbound HTTP metrics for the service.

Wraps the request pipeline and records per-service request counts and duration
into an inbound HTTP metrics recorder (a MetricsRegistry backed adapter). The
``/metrics`` path is excluded so scrapes do not pollute their own output.
"""

from __future__ import annotations

from contextlib import suppress
from time import perf_counter
from typing import TYPE_CHECKING, Any

from shell.platform.observability.application.ports.metrics import InboundHttpMetricsRecorder

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from starlette.types import ASGIApp, Receive, Scope, Send


class MetricsMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        recorder: InboundHttpMetricsRecorder,
        *,
        service: str = "",
    ) -> None:
        self.app = app
        self._recorder = recorder
        self._service = service
        self._skipped_paths = frozenset({"/metrics"})

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        if scope.get("path", "") in self._skipped_paths:
            await self.app(scope, receive, send)
            return

        start = perf_counter()
        status: dict[str, int] = {"code": 500}

        async def send_wrapper(message: MutableMapping[str, Any]) -> None:
            if message["type"] == "http.response.start":
                status_value = message.get("status", 500)
                if isinstance(status_value, int):
                    status["code"] = status_value
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = perf_counter() - start
            method = str(scope.get("method", "GET"))
            self._record_inbound(method, status["code"], duration)

    def _record_inbound(self, method: str, status: int, duration: float) -> None:
        with suppress(Exception):
            self._recorder.record_inbound_request(
                service=self._service,
                method=method,
                status=status,
                duration_seconds=duration,
            )
