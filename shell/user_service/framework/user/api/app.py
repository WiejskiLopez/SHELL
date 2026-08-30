"""FastAPI application factory — BC User."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI

from shell.platform.domain.exceptions import DomainError
from shell.platform.framework.api.middleware.api_key import AuthMiddleware
from shell.platform.framework.api.middleware.correlation_id import (
    CorrelationIdMiddleware,
)
from shell.platform.framework.api.middleware.error_handler import domain_error_handler
from shell.platform.framework.api.openapi import configure_openapi
from shell.platform.observability.framework.api.health import mount_readiness
from shell.platform.observability.framework.api.metrics import install_metrics
from shell.platform.observability.framework.api.providers import ObservabilityProviders
from shell.user_service.application.user.auth_session.queries.get_current_auth_session_query import (
    GetCurrentAuthSessionQuery,
)
from shell.user_service.framework.user.auth_session.api.router import router as auth_sessions_router
from shell.user_service.framework.user.user.api.router import router as users_router

if TYPE_CHECKING:
    from collections.abc import Collection

    from shell.platform.framework.api.dependencies import ContainerProtocol


USER_PUBLIC_EXACT = frozenset(
    {
        "/health",
        "/readiness",
        "/metrics",
        "/api",
        "/api/v1/auth_session/login",
    }
)
USER_PUBLIC_PREFIX = frozenset({"/docs", "/redoc", "/openapi.json"})
USER_OPENAPI_TAGS = (
    {"name": "Users", "description": "User management operations."},
    {"name": "AuthSessions", "description": "Authentication session operations."},
    {"name": "Health", "description": "Service health and readiness."},
)


def create_user_app(
    core_container: ContainerProtocol,
    *,
    api_key: str = "",
    jwt_secret: str = "",
    public_exact: Collection[str] | None = None,
    public_prefix: Collection[str] | None = None,
) -> FastAPI:
    """Tworzy aplikację FastAPI dla BC User."""
    app = FastAPI(title="shell — user", version="0.1.0")
    app.state.core_container = core_container

    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        AuthMiddleware,
        api_key=api_key,
        jwt_secret=jwt_secret,
        session_query_factory=lambda token: GetCurrentAuthSessionQuery(token=token),
        public_exact=USER_PUBLIC_EXACT if public_exact is None else public_exact,
        public_prefix=USER_PUBLIC_PREFIX if public_prefix is None else public_prefix,
    )
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]

    app.include_router(users_router, prefix="/api/v1")
    app.include_router(auth_sessions_router, prefix="/api/v1")
    configure_openapi(app, tags=USER_OPENAPI_TAGS)
    providers = ObservabilityProviders.from_container(core_container)
    mount_readiness(app, providers)
    install_metrics(app, providers, service="user")

    @app.get("/health", tags=["Health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
