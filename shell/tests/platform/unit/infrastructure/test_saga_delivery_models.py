"""Unit tests for saga persistence models (saga_instance + saga_timeout)."""

from __future__ import annotations

from typing import Any, cast

from sqlalchemy import MetaData, Table, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase

from shell.platform.domain.value_objects.inbox_status import InboxStatus
from shell.platform.infrastructure.persistence.sql.models.persistence_delivery import (
    build_persistence_delivery_models,
)
from shell.platform.infrastructure.process.saga.models.saga_delivery import (
    build_saga_delivery_models,
)
from shell.platform.process.saga.base.saga_state import SagaStatus

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

_INSTANCE_COLUMNS = (
    "id",
    "saga_type",
    "saga_key",
    "status",
    "current_step",
    "business_payload",
    "completed_steps",
    "failed_steps",
    "version",
    "created_at",
    "updated_at",
)


def _new_base() -> type[DeclarativeBase]:
    class TestBase(DeclarativeBase):
        metadata = MetaData()

    return TestBase


class TestSagaDeliveryModels:
    def test_persistence_bundle_includes_saga_tables(self) -> None:
        base = _new_base()
        bundle = build_persistence_delivery_models(base)
        instance_table = cast("Any", bundle.sagas.instance).__table__
        timeout_table = cast("Any", bundle.sagas.timeout).__table__
        assert instance_table.name == "saga_instance"
        assert timeout_table.name == "saga_timeout"
        assert instance_table.metadata is base.metadata
        assert timeout_table.metadata is base.metadata

    def test_saga_instance_has_core_columns(self) -> None:
        models = build_saga_delivery_models(_new_base())
        columns = models.instance.__table__.columns.keys()
        assert all(name in columns for name in _INSTANCE_COLUMNS)

    def test_saga_instance_status_default_is_running(self) -> None:
        models = build_saga_delivery_models(_new_base())
        status_default = models.instance.__table__.c.status.default
        assert status_default is not None
        assert status_default.arg == SagaStatus.RUNNING.value
        version_default = models.instance.__table__.c.version.default
        assert version_default is not None
        assert version_default.arg == 1

    def test_saga_instance_has_unique_type_key(self) -> None:
        models = build_saga_delivery_models(_new_base())
        table = cast("Table", models.instance.__table__)
        unique_names = {
            constraint.name
            for constraint in table.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        assert "uq_saga_instance_type_key" in unique_names

    def test_saga_timeout_has_operational_columns(self) -> None:
        models = build_saga_delivery_models(_new_base())
        assert _OPERATIONAL_COLUMNS.issubset(models.timeout.__table__.columns.keys())
        status_default = models.timeout.__table__.c.status.default
        assert status_default is not None
        assert status_default.arg == InboxStatus.PENDING.value

    def test_saga_timeout_has_processing_columns(self) -> None:
        models = build_saga_delivery_models(_new_base())
        for column in ("outbox_id", "saga_id", "saga_key", "step", "due_at", "received_at"):
            assert column in models.timeout.__table__.columns

    def test_saga_timeout_indexes_are_table_specific(self) -> None:
        models = build_saga_delivery_models(_new_base())
        table = cast("Table", models.timeout.__table__)
        index_names = {index.name for index in table.indexes}
        assert "ix_saga_timeout_status_next_attempt_received" in index_names
        assert "ix_saga_timeout_status_lease_until" in index_names
