"""Compatibility exports for application ports."""

from __future__ import annotations

from shell.platform.application.ports.delivery_transport import (
    DeliveryEnvelope,
    DeliveryTransport,
)
from shell.platform.application.ports.logger import Logger
from shell.platform.application.ports.messaging import EventPublisher
from shell.platform.application.ports.unit_of_work import UnitOfWork
from shell.platform.domain.ports.identity import IdGenerator
from shell.platform.domain.ports.time import Clock

__all__ = [
    "Clock",
    "DeliveryEnvelope",
    "DeliveryTransport",
    "EventPublisher",
    "IdGenerator",
    "Logger",
    "UnitOfWork",
]
