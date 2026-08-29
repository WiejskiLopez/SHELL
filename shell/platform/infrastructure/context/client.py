from __future__ import annotations

import asyncio
import os
import random
import ssl
import time
from typing import TYPE_CHECKING, Any

import httpx

from shell.platform.application.authentication.request_signing import (
    SIGNATURE_HEADER,
    TIMESTAMP_HEADER,
    sign_request,
)
from shell.platform.application.context.correlation_id import get_correlation_id
from shell.platform.infrastructure.context.resilience import (
    CircuitBreaker,
    CircuitBreakerPolicy,
    CircuitOpenError,
    CircuitState,
    RetryPolicy,
)

if TYPE_CHECKING:
    from shell.platform.observability.application.ports.metrics import (
        OutboundHttpMetricsRecorder,
    )


def client_tls_kwargs_from_env(service: str = "") -> dict[str, Any]:
    """Resolve optional per-service client certificate authentication from the environment.

    Preferences:
    - ``{SERVICE}_SERVICE_MTLS_CA_CERTS`` / ``_CERTFILE`` / ``_KEYFILE`` when ``service``
      is provided (per-service identity, e.g. ``EXECUTION_SERVICE_MTLS_*``);
    - legacy shared ``SHELL_MTLS_*`` when ``service`` is empty.
    """
    prefix = f"{service.upper()}_SERVICE_MTLS" if service else "SHELL_MTLS"
    ca_certs = os.environ.get(f"{prefix}_CA_CERTS", "")
    certfile = os.environ.get(f"{prefix}_CERTFILE", "")
    keyfile = os.environ.get(f"{prefix}_KEYFILE", "")
    if not ca_certs and not certfile and not keyfile:
        return {}
    if not ca_certs or not certfile or not keyfile:
        raise ValueError(f"{prefix} requires _CA_CERTS, _CERTFILE and _KEYFILE to be set together")
    context = ssl.create_default_context(cafile=ca_certs)
    context.load_cert_chain(certfile, keyfile)
    return {"verify": context}


class CorrelationIdAsyncClient(httpx.AsyncClient):
    """Async HTTP client that automatically injects the X-Correlation-ID header
    from the current execution context into every outgoing request."""

    def __init__(self, *, service_api_key: str = "", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._service_api_key = service_api_key

    async def request(self, method: str, url: httpx.URL | str, **kwargs: Any) -> httpx.Response:
        corr_id = get_correlation_id()
        if corr_id or self._service_api_key:
            headers = kwargs.get("headers", {})
            if headers is None:
                headers = {}
            elif not isinstance(headers, dict):
                headers = dict(headers)
            if corr_id:
                headers.setdefault("X-Correlation-ID", corr_id)
            if self._service_api_key:
                headers.setdefault("X-API-Key", self._service_api_key)
                self._add_signature_headers(headers, method, url)
            kwargs["headers"] = headers
        return await super().request(method, url, **kwargs)

    @staticmethod
    def _signature_path(url: httpx.URL | str) -> str:
        if isinstance(url, httpx.URL):
            return url.path
        return str(url).split("?", 1)[0]

    def _add_signature_headers(
        self,
        headers: dict[str, str],
        method: str,
        url: httpx.URL | str,
    ) -> None:
        from time import time

        timestamp = int(time())
        headers.setdefault(
            SIGNATURE_HEADER,
            sign_request(
                secret=self._service_api_key,
                method=method,
                path=self._signature_path(url),
                timestamp=timestamp,
            ),
        )
        headers.setdefault(TIMESTAMP_HEADER, str(timestamp))


class ResilientAsyncClient(CorrelationIdAsyncClient):
    """HTTP client with bounded retries and a per-client circuit breaker."""

    def __init__(
        self,
        *,
        retry_policy: RetryPolicy | None = None,
        circuit_breaker_policy: CircuitBreakerPolicy | None = None,
        clock: Any = time.monotonic,
        sleeper: Any = asyncio.sleep,
        random_uniform: Any = random.uniform,
        metrics: OutboundHttpMetricsRecorder | None = None,
        metrics_target: str = "",
        tls_identity: str = "",
        **kwargs: Any,
    ) -> None:
        kwargs.update(client_tls_kwargs_from_env(tls_identity))
        super().__init__(**kwargs)
        self._retry_policy = retry_policy or RetryPolicy()
        self._circuit_breaker = CircuitBreaker(circuit_breaker_policy or CircuitBreakerPolicy())
        self._metrics = metrics
        self._metrics_target = metrics_target
        self._clock = clock
        self._sleeper = sleeper
        self._random_uniform = random_uniform

    def _record(self, name: str, *, method: str, **kwargs: Any) -> None:
        if self._metrics is None:
            return
        try:
            recorder = getattr(self._metrics, name)
            recorder(
                target_service=self._metrics_target,
                method=method,
                **kwargs,
            )
        except Exception:
            return

    def _record_breaker_after_failure(self, method: str) -> None:
        if self._circuit_breaker.state is CircuitState.OPEN:
            self._record("record_circuit_trip", method=method)
        self._record(
            "record_circuit_state",
            method=method,
            state=self._circuit_breaker.state.value,
        )

    @property
    def circuit_state(self) -> str:
        return self._circuit_breaker.state.value

    async def request(self, method: str, url: httpx.URL | str, **kwargs: Any) -> httpx.Response:
        normalized_method = method.upper()
        if not self._circuit_breaker.allow_request(self._clock()):
            self._record("record_circuit_reject", method=normalized_method)
            raise CircuitOpenError(f"HTTP circuit is open for {self.base_url}")

        can_retry = normalized_method in self._retry_policy.retryable_methods
        for attempt in range(1, self._retry_policy.max_attempts + 1):
            self._record("record_outbound_attempt", method=normalized_method)
            try:
                response = await super().request(method, url, **kwargs)
            except httpx.TransportError:
                if can_retry and attempt < self._retry_policy.max_attempts:
                    self._record("record_outbound_retry", method=normalized_method)
                    await self._wait_before_retry(attempt)
                    continue
                self._circuit_breaker.record_failure(self._clock())
                self._record_breaker_after_failure(normalized_method)
                raise

            should_retry = response.status_code in self._retry_policy.retryable_statuses
            if should_retry and can_retry and attempt < self._retry_policy.max_attempts:
                self._record("record_outbound_retry", method=normalized_method)
                await response.aclose()
                await self._wait_before_retry(attempt)
                continue

            if 200 <= response.status_code < 400:
                self._circuit_breaker.record_success()
                self._record(
                    "record_circuit_state",
                    method=normalized_method,
                    state=self._circuit_breaker.state.value,
                )
            elif response.status_code >= 500 or response.status_code == 429:
                self._circuit_breaker.record_failure(self._clock())
                self._record_breaker_after_failure(normalized_method)
            return response

        raise RuntimeError("HTTP request loop exited unexpectedly")

    async def _wait_before_retry(self, attempt: int) -> None:
        delay = min(
            self._retry_policy.max_delay,
            self._retry_policy.initial_delay * (2 ** (attempt - 1)),
        )
        if self._retry_policy.jitter:
            delay += self._random_uniform(0, self._retry_policy.jitter)
        if delay:
            await self._sleeper(delay)
