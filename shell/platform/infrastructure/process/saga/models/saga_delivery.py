"""Factory for per-service saga persistence models (instance + timeout)."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves Mapped[...] at class definition
from typing import Any, NamedTuple

from sqlalchemy import DateTime, Index, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

from shell.platform.infrastructure.persistence.sql.models._compat import JSONB
from shell.platform.infrastructure.persistence.sql.models.mixins.inbox_state import (
    InboxStateMixin,
    build_inbox_state_indexes,
)
from shell.platform.process.saga.base.saga_state import SagaStatus


class SagaDeliveryModels(NamedTuple):
    instance: type[DeclarativeBase]
    timeout: type[DeclarativeBase]


def build_saga_delivery_models(base: type[DeclarativeBase]) -> SagaDeliveryModels:
    """Build ``saga_instance`` and ``saga_timeout`` bound to one BC metadata registry."""

    class SagaInstanceModel(base):  # type: ignore[misc, valid-type]
        __tablename__ = "saga_instance"

        @declared_attr  # type: ignore[arg-type]
        def __table_args__(cls: type[Any]) -> tuple[object, ...]:
            return (
                UniqueConstraint("saga_type", "saga_key", name="uq_saga_instance_type_key"),
                Index("ix_saga_instance_status_current", "status", "current_step"),
            )

        id: Mapped[str] = mapped_column(primary_key=True)
        saga_type: Mapped[str] = mapped_column(nullable=False)
        saga_key: Mapped[str] = mapped_column(nullable=False)
        status: Mapped[str] = mapped_column(nullable=False, default=SagaStatus.RUNNING.value)
        current_step: Mapped[str | None] = mapped_column(nullable=True, default=None)
        business_payload: Mapped[dict[str, object]] = mapped_column(
            JSONB, nullable=False, default=dict
        )
        completed_steps: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
        failed_steps: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
        version: Mapped[int] = mapped_column(nullable=False, default=1)
        created_at: Mapped[datetime | None] = mapped_column(
            DateTime(timezone=True), nullable=True, default=None
        )
        updated_at: Mapped[datetime | None] = mapped_column(
            DateTime(timezone=True), nullable=True, default=None
        )
        completed_at: Mapped[datetime | None] = mapped_column(
            DateTime(timezone=True), nullable=True, default=None
        )
        failed_at: Mapped[datetime | None] = mapped_column(
            DateTime(timezone=True), nullable=True, default=None
        )
        compensated_at: Mapped[datetime | None] = mapped_column(
            DateTime(timezone=True), nullable=True, default=None
        )

    class SagaTimeoutModel(InboxStateMixin, base):  # type: ignore[misc, valid-type]
        __tablename__ = "saga_timeout"

        @declared_attr  # type: ignore[arg-type]
        def __table_args__(cls: type[Any]) -> tuple[Index | UniqueConstraint, ...]:
            return (
                UniqueConstraint(
                    "source_service",
                    "outbox_id",
                    name="uq_saga_timeout_source_outbox",
                ),
                *build_inbox_state_indexes(cls.__tablename__),
            )

        id: Mapped[str] = mapped_column(primary_key=True)
        outbox_id: Mapped[str] = mapped_column(nullable=False)
        saga_id: Mapped[str] = mapped_column(nullable=False)
        saga_key: Mapped[str] = mapped_column(nullable=False)
        step: Mapped[str] = mapped_column(nullable=False)
        source_service: Mapped[str] = mapped_column(nullable=False)
        due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
        payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
        correlation_id: Mapped[str] = mapped_column(nullable=False, default="")
        causation_id: Mapped[str] = mapped_column(nullable=False, default="")
        received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    SagaInstanceModel.__name__ = f"{base.__name__}SagaInstanceModel"
    SagaInstanceModel.__qualname__ = SagaInstanceModel.__name__
    SagaTimeoutModel.__name__ = f"{base.__name__}SagaTimeoutModel"
    SagaTimeoutModel.__qualname__ = SagaTimeoutModel.__name__

    return SagaDeliveryModels(instance=SagaInstanceModel, timeout=SagaTimeoutModel)
