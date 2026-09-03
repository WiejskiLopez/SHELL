"""Unit tests — CorrelationIdMiddleware generates/sets the correlation id."""

from __future__ import annotations

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from shell.platform.application.context.correlation_id import (
    reset_correlation_id,
    set_correlation_id,
    set_correlation_id_generator,
)
from shell.platform.framework.api.middleware.correlation_id import CorrelationIdMiddleware
from shell.platform.infrastructure.identity.static_correlation_id_generator import (
    StaticCorrelationIdGenerator,
)


def _app() -> FastAPI:
    app = FastAPI()

    @app.get("/echo")
    async def echo() -> dict[str, str]:
        return {"ok": "1"}

    app.add_middleware(CorrelationIdMiddleware)
    return app


class TestCorrelationIdMiddleware:
    async def test_uses_incoming_header_when_present(self) -> None:
        app = _app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/echo", headers={"X-Correlation-ID": "given-123"})
        assert response.status_code == 200
        assert response.headers["X-Correlation-ID"] == "given-123"

    async def test_generates_when_header_absent(self) -> None:
        set_correlation_id_generator(StaticCorrelationIdGenerator(prefix="gen-"))
        # autouse conftest fixture wypełnia kontekst testowym id — wyczyść go,
        # aby przećwiczyć gałąź generowania w middleware.
        token = set_correlation_id("")
        try:
            app = _app()
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/echo")
        finally:
            reset_correlation_id(token)
        assert response.status_code == 200
        assert response.headers["X-Correlation-ID"].startswith("gen-")
        assert response.headers["X-Correlation-ID"] != ""
