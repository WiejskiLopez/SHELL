"""SQL ORM model <-> domain entity mappers for Workflow aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from shell.platform.domain.value_objects.created_at import CreatedAt
    from shell.platform.domain.value_objects.deleted_at import DeletedAt


def _created_at_value(dt: CreatedAt | DeletedAt | datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt.value if hasattr(dt, "value") else dt
