"""Re-eksportuje platformowe QueryService klasy."""

from __future__ import annotations

from shell.platform.infrastructure.persistence.sql.services.message_router_query_service import (
    MessageRouterQueryService,
)

__all__ = [
    "MessageRouterQueryService",
]
