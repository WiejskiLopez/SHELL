"""Factory for the ``worker_heartbeat`` model.

A long-lived polling worker records its heartbeat (``worker_id`` + ``last_seen_at``)
here so readiness probes can tell a live worker from a dead one — lease holders
alone are not proof of liveness (ref4.md Krok 4). The worker_id is the primary key,
so one row exists per worker process/configuration.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] requires runtime type

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def build_worker_heartbeat_model(base: type[DeclarativeBase]) -> type[DeclarativeBase]:
    """Build the ``worker_heartbeat`` ORM model bound to one BC metadata registry."""

    class WorkerHeartbeatModel(base):  # type: ignore[misc, valid-type]
        __tablename__ = "worker_heartbeat"

        worker_id: Mapped[str] = mapped_column(primary_key=True)
        last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    WorkerHeartbeatModel.__name__ = f"{base.__name__}WorkerHeartbeatModel"
    WorkerHeartbeatModel.__qualname__ = WorkerHeartbeatModel.__name__

    return WorkerHeartbeatModel
