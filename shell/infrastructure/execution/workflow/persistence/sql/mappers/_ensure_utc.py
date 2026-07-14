"""SQL ORM model <-> domain entity mappers for Workflow aggregate."""

from __future__ import annotations

from datetime import UTC, datetime


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt

