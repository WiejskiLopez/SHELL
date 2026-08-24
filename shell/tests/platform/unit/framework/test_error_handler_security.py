from __future__ import annotations

import json
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest

from shell.platform.framework.api.middleware.error_handler import unhandled_exception_handler

if TYPE_CHECKING:
    from fastapi import Request


@pytest.mark.asyncio
async def test_unhandled_error_response_does_not_expose_exception_details() -> None:
    response = await unhandled_exception_handler(
        cast("Request", SimpleNamespace()),
        RuntimeError("database password=super-secret"),
    )

    body = json.loads(bytes(response.body))
    body_bytes = bytes(response.body)

    assert response.status_code == 500
    assert body["title"] == "Internal Server Error"
    assert body["detail"] == "An unexpected error occurred"
    assert "super-secret" not in body_bytes.decode()
