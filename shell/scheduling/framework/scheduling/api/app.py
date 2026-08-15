from __future__ import annotations

from fastapi import FastAPI

from shell.platform.framework.api.health import mount_readiness
from shell.scheduling.framework.scheduling.scheduler_definition.api.router import (
    router as scheduler_definition_router,
)
from shell.scheduling.framework.scheduling.scheduler_execution.api.router import (
    router as scheduler_execution_router,
)
from shell.scheduling.framework.scheduling.scheduler_job.api.router import (
    router as scheduler_job_router,
)


def create_scheduling_app(container: object | None = None) -> FastAPI:
    app = FastAPI(title="shell - scheduling", version="0.1.0")
    if container is not None:
        app.state.core_container = container
        app.include_router(scheduler_definition_router, prefix="/api/v1")
        app.include_router(scheduler_execution_router, prefix="/api/v1")
        app.include_router(scheduler_job_router, prefix="/api/v1")

    @app.get("/health", tags=["Health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    if container is not None:
        mount_readiness(app, container)

    return app
