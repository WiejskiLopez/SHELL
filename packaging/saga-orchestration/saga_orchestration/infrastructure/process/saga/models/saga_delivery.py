from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves Mapped annotations
from typing import Any, NamedTuple

from sqlalchemy import JSON, DateTime, Index, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

from saga_orchestration.process.saga.base.saga_state import SagaStatus


class SagaDeliveryModels(NamedTuple):
    instance: type[DeclarativeBase]
    timeout: type[DeclarativeBase]


class SagaTimeoutStateMixin:
    @declared_attr
    def __table_args__(cls: type[Any]) -> tuple[Index, ...]:
        return (
            Index(
                "ix_saga_timeout_status_next_attempt_received",
                "status",
                "next_attempt_at",
                "received_at",
            ),
            Index("ix_saga_timeout_status_lease_until", "status", "lease_until"),
        )

    status: Mapped[str] = mapped_column(nullable=False, default="PENDING")
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    claimed_by: Mapped[str | None] = mapped_column(nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_attempted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    retry_count: Mapped[int] = mapped_column(nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(nullable=True)
    error_code: Mapped[str | None] = mapped_column(nullable=True)
    error_message: Mapped[str | None] = mapped_column(nullable=True)
    schema_version: Mapped[int] = mapped_column(nullable=False, default=1)


def build_saga_delivery_models(base: type[DeclarativeBase]) -> SagaDeliveryModels:
    class SagaInstanceModel(base):  # type: ignore[misc, valid-type]
        __tablename__ = "saga_instance"

        @declared_attr
        def __table_args__(cls: type[Any]) -> tuple[object, ...]:
            return (
                UniqueConstraint("saga_type", "saga_key", name="uq_saga_instance_type_key"),
                Index("ix_saga_instance_status_current", "status", "current_step"),
            )

        id: Mapped[str] = mapped_column(primary_key=True)
        saga_type: Mapped[str] = mapped_column(nullable=False)
        saga_key: Mapped[str] = mapped_column(nullable=False)
        status: Mapped[str] = mapped_column(nullable=False, default=SagaStatus.RUNNING.value)
        current_step: Mapped[str | None] = mapped_column(nullable=True)
        business_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
        completed_steps: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
        failed_steps: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
        version: Mapped[int] = mapped_column(nullable=False, default=1)
        created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
        updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
        completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
        failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
        compensated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    class SagaTimeoutModel(SagaTimeoutStateMixin, base):  # type: ignore[misc, valid-type]
        __tablename__ = "saga_timeout"

        id: Mapped[str] = mapped_column(primary_key=True)
        saga_id: Mapped[str] = mapped_column(nullable=False)
        saga_key: Mapped[str] = mapped_column(nullable=False)
        step: Mapped[str] = mapped_column(nullable=False)
        outbox_id: Mapped[str] = mapped_column(nullable=False)
        source_service: Mapped[str] = mapped_column(nullable=False)
        due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
        payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
        correlation_id: Mapped[str] = mapped_column(nullable=False, default="")
        causation_id: Mapped[str] = mapped_column(nullable=False, default="")
        received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    SagaInstanceModel.__name__ = f"{base.__name__}SagaInstanceModel"
    SagaTimeoutModel.__name__ = f"{base.__name__}SagaTimeoutModel"
    return SagaDeliveryModels(SagaInstanceModel, SagaTimeoutModel)
