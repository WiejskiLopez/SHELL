"""Factory for a per-service audit event model."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves Mapped[...] at class definition

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from shell.platform.infrastructure.persistence.sql.models._compat import JSONB


def build_audit_event_model(base: type[DeclarativeBase]) -> type[DeclarativeBase]:
    """Build an audit event model bound to one BC metadata registry."""

    class AuditEventModel(base):  # type: ignore[misc, valid-type]
        __tablename__ = "audit_event"

        id: Mapped[str] = mapped_column(primary_key=True)
        integration_event_name: Mapped[str] = mapped_column(nullable=False)
        occurred_at: Mapped[datetime] = mapped_column(nullable=False)
        payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)

    AuditEventModel.__name__ = f"{base.__name__}AuditEventModel"
    AuditEventModel.__qualname__ = AuditEventModel.__name__
    return AuditEventModel
