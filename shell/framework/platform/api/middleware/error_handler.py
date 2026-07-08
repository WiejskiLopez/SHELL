"""Error handler middleware — maps DomainErrors to 4xx HTTP responses.

BC-specific exception mappings should be added via per-BC middleware.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse

from shell.domain.platform.exceptions import (
    DomainError,  # noqa: TC001 — potrzebny w runtime dla isinstance() i handlera wyjątków
)
from shell.domain.platform.exceptions.concurrent_modification_error import (
    ConcurrentModificationError,
)

if TYPE_CHECKING:
    from fastapi import Request


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    if isinstance(exc, ConcurrentModificationError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})
    return JSONResponse(status_code=400, content={"detail": str(exc)})
