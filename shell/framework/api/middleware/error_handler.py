"""Error handler middleware — maps DomainErrors to 4xx HTTP responses."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse

from shell.domain.exceptions import (
    DomainError,
    EnvelopeNotFound,
    NodeNotFound,
    PromptNotFound,
    RunnerConfigNotFound,
    TaskNotFound,
    WorkflowNotFound,
)

if TYPE_CHECKING:
    from fastapi import Request

_NOT_FOUND = {
    TaskNotFound,
    WorkflowNotFound,
    EnvelopeNotFound,
    NodeNotFound,
    PromptNotFound,
    RunnerConfigNotFound,
}


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    status = 404 if type(exc) in _NOT_FOUND else 400
    return JSONResponse(status_code=status, content={"detail": str(exc)})
