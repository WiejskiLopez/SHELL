"""Error handler middleware — maps DomainErrors to 4xx HTTP responses."""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from shell_ddd.domain.exceptions import (
    DomainError,
    EnvelopeNotFound,
    NodeNotFound,
    PromptNotFound,
    RunnerConfigNotFound,
    TaskNotFound,
    WorkflowNotFound,
)

_NOT_FOUND = {TaskNotFound, WorkflowNotFound, EnvelopeNotFound, NodeNotFound, PromptNotFound, RunnerConfigNotFound}


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    status = 404 if type(exc) in _NOT_FOUND else 400
    return JSONResponse(status_code=status, content={"detail": str(exc)})
