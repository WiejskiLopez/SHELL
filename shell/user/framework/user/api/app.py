"""FastAPI application factory — BC User."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI

from shell.platform.domain.exceptions import DomainError
from shell.platform.framework.api.health import mount_readiness
from shell.platform.framework.api.middleware.api_key import AuthMiddleware
from shell.platform.framework.api.middleware.correlation_id import (
    CorrelationIdMiddleware,
)
from shell.platform.framework.api.middleware.error_handler import domain_error_handler
from shell.user.application.user.auth_session.queries.get_current_auth_session_query import (
    GetCurrentAuthSessionQuery,
)
from shell.user.framework.user.auth_session.api.router import router as auth_sessions_router
from shell.user.framework.user.user.api.router import router as users_router

if TYPE_CHECKING:
    from shell.platform.framework.api.dependencies import ContainerProtocol


def create_user_app(
    core_container: ContainerProtocol,
    *,
    api_key: str = "",
    jwt_secret: str = "",
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
    )
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]

    app.include_router(users_router, prefix="/api/v1")
    app.include_router(auth_sessions_router, prefix="/api/v1")
    mount_readiness(app, core_container)

    @app.get("/health", tags=["Health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
