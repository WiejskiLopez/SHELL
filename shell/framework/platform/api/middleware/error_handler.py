"""Error handler middleware — maps DomainErrors to 4xx HTTP responses."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from shell.domain.definition.exceptions import RunnerConfigNotFound
from shell.domain.execution.exceptions import (
    EnvelopeNotFound,
    NodeNotFound,
    TaskExecutionNotFound,
    WorkflowNotFound,
)
from shell.domain.platform.exceptions import (
    DomainError,  # noqa: TC002 — DomainError używany w sygnaturze domain_error_handler() i isinstance() w _NOT_FOUND
)

if TYPE_CHECKING:
    from fastapi import Request

_NOT_FOUND = {
    TaskExecutionNotFound,
    WorkflowNotFound,
    EnvelopeNotFound,
    NodeNotFound,
    RunnerConfigNotFound,
}


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    status = 404 if type(exc) in _NOT_FOUND else 400
    return JSONResponse(status_code=status, content={"detail": str(exc)})
