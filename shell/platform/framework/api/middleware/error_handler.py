"""Error handler middleware — maps DomainErrors to 4xx HTTP responses.

BC-specific exception mappings should be added via per-BC middleware.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse

from shell.platform.domain.exceptions import (
    DomainError,  # noqa: TC001 — potrzebny w runtime dla isinstance() i handlera wyjątków
)
from shell.platform.domain.exceptions.concurrent_modification_error import (
    ConcurrentModificationError,
)
from shell.platform.framework.api.models.problem_detail import FieldError, ProblemDetail

if TYPE_CHECKING:
    from fastapi import HTTPException, Request
    from fastapi.exceptions import RequestValidationError


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    if isinstance(exc, ConcurrentModificationError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})
    return JSONResponse(status_code=400, content={"detail": str(exc)})


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ProblemDetail(
            title=exc.detail,
            status=exc.status_code,
            detail=exc.detail,
            timestamp=ProblemDetail.now_iso(),
        ).model_dump(),
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        FieldError(
            field=".".join(str(x) for x in err.get("loc", [])),
            message=err.get("msg", ""),
            code=err.get("type", ""),
        )
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=ProblemDetail(
            title="Validation Error",
            status=422,
            detail="Request validation failed",
            errors=errors,
            timestamp=ProblemDetail.now_iso(),
        ).model_dump(),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=ProblemDetail(
            title="Internal Server Error",
            status=500,
            detail="An unexpected error occurred",
            timestamp=ProblemDetail.now_iso(),
        ).model_dump(),
    )
