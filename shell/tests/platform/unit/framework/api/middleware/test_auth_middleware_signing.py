"""Unit tests — AuthMiddleware accepts valid HMAC-signed SYSTEM requests."""

from __future__ import annotations

import time

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from shell.platform.application.authentication.request_signing import (
    SIGNATURE_HEADER,
    TIMESTAMP_HEADER,
    sign_request,
)
from shell.platform.framework.api.middleware.api_key import AuthMiddleware

API_KEY = "service-shared-secret"


def _app() -> FastAPI:
    app = FastAPI()

    @app.get("/protected")
    async def protected() -> dict[str, str]:
        return {"ok": "1"}

    app.add_middleware(
        AuthMiddleware,
        api_key=API_KEY,
        public_exact=set(),
        public_prefix=set(),
    )
    return app


class TestAuthMiddlewareSigning:
    async def test_valid_signature_authorizes_system(self) -> None:
        app = _app()
        timestamp = int(time.time())
        signature = sign_request(
            secret=API_KEY, method="GET", path="/protected", timestamp=timestamp
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/protected",
                headers={
                    SIGNATURE_HEADER: signature,
                    TIMESTAMP_HEADER: str(timestamp),
                },
            )

        assert response.status_code == 200

    async def test_tampered_signature_is_rejected(self) -> None:
        app = _app()
        timestamp = int(time.time())
        signature = sign_request(
            secret=API_KEY, method="GET", path="/protected", timestamp=timestamp
        )
        tampered = ("b" if not signature.startswith("b") else "a") + signature[1:]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/protected",
                headers={
                    SIGNATURE_HEADER: tampered,
                    TIMESTAMP_HEADER: str(timestamp),
                },
            )

        assert response.status_code == 401

    async def test_stale_signature_is_rejected(self) -> None:
        app = _app()
        stale_timestamp = int(time.time()) - 10_000
        signature = sign_request(
            secret=API_KEY, method="GET", path="/protected", timestamp=stale_timestamp
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/protected",
                headers={
                    SIGNATURE_HEADER: signature,
                    TIMESTAMP_HEADER: str(stale_timestamp),
                },
            )

        assert response.status_code == 401

    async def test_missing_signature_is_rejected(self) -> None:
        app = _app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/protected")

        assert response.status_code == 401
