from __future__ import annotations

import os
from typing import TYPE_CHECKING

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from shell.platform.domain.exceptions import DomainError
from shell.platform.framework.api.constants import API_VERSION_REGISTRY
from shell.platform.framework.api.middleware.api_version import ApiVersionMiddleware
from shell.platform.framework.api.middleware.audit_log import AuditLogMiddleware
from shell.platform.framework.api.middleware.correlation_id import CorrelationIdMiddleware
from shell.platform.framework.api.middleware.error_handler import (
    domain_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_error_handler,
)
from shell.platform.framework.api.models.page import Page
from shell.platform.framework.api.models.problem_detail import FieldError, ProblemDetail

if TYPE_CHECKING:
    from shell.platform.framework.api.version import ApiVersionRegistry


def resolve_api_key(container: object | None = None) -> str:
    if container is not None:
        try:
            config = getattr(container, "config", None)
            if config is not None:
                key_provider = getattr(config, "api_key", None)
                if key_provider is not None:
                    value = key_provider() if callable(key_provider) else key_provider
                    if value:
                        return value
        except (ValueError, AttributeError):
            pass
    return os.environ.get("SHELL_API_KEY", "")


def resolve_jwt_secret(container: object | None = None) -> str:
    if container is not None:
        try:
            config = getattr(container, "config", None)
            if config is not None:
                secret_provider = getattr(config, "jwt_secret", None)
                if secret_provider is not None:
                    value = secret_provider() if callable(secret_provider) else secret_provider
                    if value:
                        return value
        except (ValueError, AttributeError):
            pass
    return os.environ.get("SHELL_JWT_SECRET", "")


def _register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)


def _inject_common_schemas(app: FastAPI) -> None:
    def custom_openapi() -> dict[str, object]:
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
        )
        openapi_schema.setdefault("components", {}).setdefault("schemas", {}).update(
            {
                "ProblemDetail": ProblemDetail.model_json_schema(),
                "Page": Page.model_json_schema(),
                "FieldError": FieldError.model_json_schema(),
            }
        )
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[method-assign]


def setup_api_common(
    app: FastAPI,
    registry: ApiVersionRegistry = API_VERSION_REGISTRY,
    api_key: str = "",
    jwt_secret: str = "",
) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(AuditLogMiddleware)

    from shell.platform.framework.api.middleware.api_key import AuthMiddleware

    app.add_middleware(AuthMiddleware, api_key=api_key, jwt_secret=jwt_secret)

    app.add_middleware(ApiVersionMiddleware, registry=registry)

    _register_error_handlers(app)
    _inject_common_schemas(app)

    @app.get("/health", tags=["Health"])
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "api_version": registry.latest,
            "latest_version": registry.latest,
        }


def create_api_discovery_router(
    registry: ApiVersionRegistry = API_VERSION_REGISTRY,
) -> APIRouter:
    router = APIRouter(tags=["ApiDiscovery"])

    @router.get("/api")
    async def api_discovery() -> dict[str, object]:
        return {
            "versions": registry.list_versions(),
            "latest": registry.latest,
        }

    return router
