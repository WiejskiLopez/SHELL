"""Re-eksportuje platformowe QueryService klasy."""

from __future__ import annotations

from shell.infrastructure.platform.persistence.sql.services.message_query_service import (
    MessageQueryService,
)

__all__ = [
    "MessageQueryService",
]
