from __future__ import annotations

from fastapi import FastAPI

from shell.platform.framework.api.middleware.api_key import AuthMiddleware
from shell.platform.framework.api.openapi import configure_openapi
from shell.platform.observability.framework.api.health import mount_readiness
from shell.platform.observability.framework.api.metrics import install_metrics
from shell.platform.observability.framework.api.providers import ObservabilityProviders
from shell.scheduling_service.framework.scheduling.scheduler_definition.api.router import (
    router as scheduler_definition_router,
)
from shell.scheduling_service.framework.scheduling.scheduler_execution.api.router import (
    router as scheduler_execution_router,
)
from shell.scheduling_service.framework.scheduling.scheduler_job.api.router import (
    router as scheduler_job_router,
)

SCHEDULING_OPENAPI_TAGS = (
    {"name": "SchedulerDefinitions", "description": "Scheduler definition operations."},
    {"name": "SchedulerJobs", "description": "Scheduler job operations."},
    {"name": "SchedulerExecutions", "description": "Scheduler execution operations."},
    {"name": "Health", "description": "Service health and readiness."},
)


def create_scheduling_app(container: object | None = None, *, api_key: str = "") -> FastAPI:
    if not api_key:
        raise ValueError("create_scheduling_app requires a non-empty api_key (fail-closed)")
    app = FastAPI(title="shell - scheduling", version="0.1.0")
    if container is not None:
        app.state.core_container = container
        app.add_middleware(
            AuthMiddleware,
            api_key=api_key,
            public_exact={"/health", "/readiness", "/metrics"},
            public_prefix={"/docs", "/redoc", "/openapi.json"},
        )
        app.include_router(scheduler_definition_router, prefix="/api/v1")
        app.include_router(scheduler_execution_router, prefix="/api/v1")
        app.include_router(scheduler_job_router, prefix="/api/v1")
    configure_openapi(app, tags=SCHEDULING_OPENAPI_TAGS)

    @app.get("/health", tags=["Health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    if container is not None:
        providers = ObservabilityProviders.from_container(container)
        mount_readiness(app, providers)
        install_metrics(app, providers, service="scheduling")

    return app
