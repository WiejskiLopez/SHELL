"""Unit tests for the shared InboxStateMixin operational columns."""

from __future__ import annotations

from typing import cast

from sqlalchemy import MetaData, Table
from sqlalchemy.orm import DeclarativeBase

from shell.platform.domain.value_objects.inbox_status import InboxStatus
from shell.platform.infrastructure.persistence.sql.models.command_delivery import (
    build_command_delivery_models,
)
from shell.platform.infrastructure.persistence.sql.models.event_delivery import (
    build_event_delivery_models,
)

_OPERATIONAL_COLUMNS = {
    "status",
    "next_attempt_at",
    "lease_until",
    "claimed_by",
    "processed_at",
    "failed_at",
    "last_attempted_at",
    "retry_count",
    "error",
    "error_code",
    "error_message",
    "schema_version",
}


def _new_base() -> type[DeclarativeBase]:
    class TestBase(DeclarativeBase):
        metadata = MetaData()

    return TestBase


class TestInboxStateMixinColumns:
    def test_event_inbox_has_operational_columns(self) -> None:
        base = _new_base()
        models = build_event_delivery_models(base)
        assert _OPERATIONAL_COLUMNS.issubset(models.inbox.__table__.columns.keys())

    def test_command_inbox_has_operational_columns(self) -> None:
        base = _new_base()
        models = build_command_delivery_models(base)
        assert _OPERATIONAL_COLUMNS.issubset(models.inbox.__table__.columns.keys())

    def test_status_default_is_pending(self) -> None:
        base = _new_base()
        models = build_event_delivery_models(base)
        table = models.inbox.__table__
        status_default = table.c.status.default
        assert status_default is not None
        assert status_default.arg == InboxStatus.PENDING.value
        retry_default = table.c.retry_count.default
        assert retry_default is not None
        assert retry_default.arg == 0
        schema_default = table.c.schema_version.default
        assert schema_default is not None
        assert schema_default.arg == 1
        assert table.c.claimed_by.nullable
        assert table.c.lease_until.nullable

    def test_next_attempt_at_has_callable_default(self) -> None:
        base = _new_base()
        models = build_event_delivery_models(base)
        default = models.inbox.__table__.c.next_attempt_at.default
        assert default is not None
        value = default.arg(None)
        assert value is not None

    def test_indexes_are_table_specific(self) -> None:
        base = _new_base()
        event_models = build_event_delivery_models(base)
        command_models = build_command_delivery_models(base)
        event_table = cast("Table", event_models.inbox.__table__)
        command_table = cast("Table", command_models.inbox.__table__)
        event_indexes = {index.name for index in event_table.indexes}
        command_indexes = {index.name for index in command_table.indexes}
        assert "ix_inbox_event_status_next_attempt_received" in event_indexes
        assert "ix_inbox_event_status_lease_until" in event_indexes
        assert "ix_inbox_command_status_next_attempt_received" in command_indexes
        assert not event_indexes.intersection(command_indexes)
