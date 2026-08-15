"""Port: cross-cutting concerns — Logger, re-exports of shared ports."""

from __future__ import annotations

from typing import Protocol

from shell.platform.application.ports.delivery_transport import (
    DeliveryEnvelope,
    DeliveryTransport,
)
from shell.platform.application.ports.messaging import EventPublisher
from shell.platform.application.ports.unit_of_work import UnitOfWork
from shell.platform.domain.ports.identity import IdGenerator
from shell.platform.domain.ports.time import Clock


class Logger(Protocol):
    def debug(self, msg: str, **kw: object) -> None: ...
    def info(self, msg: str, **kw: object) -> None: ...
    def warning(self, msg: str, **kw: object) -> None: ...
    def error(self, msg: str, **kw: object) -> None: ...


__all__ = [
    "Clock",
    "DeliveryEnvelope",
    "DeliveryTransport",
    "EventPublisher",
    "IdGenerator",
    "Logger",
    "UnitOfWork",
]
