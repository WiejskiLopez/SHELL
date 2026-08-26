from __future__ import annotations

import asyncio
import random
import time
from typing import Any

import httpx

from shell.platform.application.context.correlation_id import get_correlation_id
from shell.platform.infrastructure.context.resilience import (
    CircuitBreaker,
    CircuitBreakerPolicy,
    CircuitOpenError,
    RetryPolicy,
)


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
            kwargs["headers"] = headers
        return await super().request(method, url, **kwargs)


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
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._retry_policy = retry_policy or RetryPolicy()
        self._circuit_breaker = CircuitBreaker(
            circuit_breaker_policy or CircuitBreakerPolicy()
        )
        self._clock = clock
        self._sleeper = sleeper
        self._random_uniform = random_uniform

    @property
    def circuit_state(self) -> str:
        return self._circuit_breaker.state.value

    async def request(self, method: str, url: httpx.URL | str, **kwargs: Any) -> httpx.Response:
        normalized_method = method.upper()
        if not self._circuit_breaker.allow_request(self._clock()):
            raise CircuitOpenError(f"HTTP circuit is open for {self.base_url}")

        can_retry = normalized_method in self._retry_policy.retryable_methods
        for attempt in range(1, self._retry_policy.max_attempts + 1):
            try:
                response = await super().request(method, url, **kwargs)
            except httpx.TransportError:
                if can_retry and attempt < self._retry_policy.max_attempts:
                    await self._wait_before_retry(attempt)
                    continue
                self._circuit_breaker.record_failure(self._clock())
                raise

            should_retry = response.status_code in self._retry_policy.retryable_statuses
            if should_retry and can_retry and attempt < self._retry_policy.max_attempts:
                await response.aclose()
                await self._wait_before_retry(attempt)
                continue

            if 200 <= response.status_code < 400:
                self._circuit_breaker.record_success()
            elif response.status_code >= 500 or response.status_code == 429:
                self._circuit_breaker.record_failure(self._clock())
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
