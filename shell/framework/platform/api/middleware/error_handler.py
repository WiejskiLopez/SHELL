"""Error handler middleware — maps DomainErrors to 4xx HTTP responses."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse

from shell.domain.definition.exceptions import RunnerConfigNotFound
from shell.domain.execution.aggregates.node_execution.exceptions.node_execution_not_found_error import (
    NodeExecutionNotFoundError,
)
from shell.domain.execution.aggregates.task_execution.exceptions.task_execution_not_found import (
    TaskExecutionNotFound,
)
from shell.domain.execution.aggregates.workflow.exceptions.workflow_not_found import (
    WorkflowNotFound,
)
from shell.domain.platform.exceptions import (
    DomainError,  # noqa: TC001 — potrzebny w runtime dla isinstance() i handlera wyjątków
)
from shell.domain.platform.exceptions.concurrent_modification_error import (
    ConcurrentModificationError,
)

if TYPE_CHECKING:
    from fastapi import Request

_NOT_FOUND = {
    TaskExecutionNotFound,
    WorkflowNotFound,
    NodeExecutionNotFoundError,
    RunnerConfigNotFound,
}


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    if isinstance(exc, ConcurrentModificationError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})
    status = 404 if type(exc) in _NOT_FOUND else 400
    return JSONResponse(status_code=status, content={"detail": str(exc)})
