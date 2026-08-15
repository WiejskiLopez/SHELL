"""Typed bundle of platform persistence models owned by one BC."""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from shell.platform.infrastructure.persistence.sql.models.audit_delivery import (
    build_audit_event_model,
)
from shell.platform.infrastructure.persistence.sql.models.command_delivery import (
    CommandDeliveryModels,
    build_command_delivery_models,
)
from shell.platform.infrastructure.persistence.sql.models.event_delivery import (
    EventDeliveryModels,
    build_event_delivery_models,
)
from shell.platform.infrastructure.persistence.sql.models.message_delivery import (
    MessageDeliveryModels,
    build_message_delivery_models,
)
from shell.platform.infrastructure.persistence.sql.models.processed_delivery import (
    build_processed_delivery_model,
)
from shell.platform.infrastructure.persistence.sql.models.worker_heartbeat import (
    build_worker_heartbeat_model,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase


class PersistenceDeliveryModels(NamedTuple):
    events: EventDeliveryModels
    messages: MessageDeliveryModels
    commands: CommandDeliveryModels
    audit: type[DeclarativeBase]
    processed_delivery: type[DeclarativeBase]
    worker_heartbeat: type[DeclarativeBase]


def build_persistence_delivery_models(
    base: type[DeclarativeBase],
) -> PersistenceDeliveryModels:
    """Build every platform persistence model bound to one BC metadata registry."""

    return PersistenceDeliveryModels(
        events=build_event_delivery_models(base),
        messages=build_message_delivery_models(base),
        commands=build_command_delivery_models(base),
        audit=build_audit_event_model(base),
        processed_delivery=build_processed_delivery_model(base),
        worker_heartbeat=build_worker_heartbeat_model(base),
    )
