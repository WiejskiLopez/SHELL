"""Integration Message base class — cross-BC contract.

All integration messages in the system inherit from this base class,
which defines the standard envelope fields including tracing context.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.exceptions import DomainError

if TYPE_CHECKING:
    from datetime import datetime

    from shell.platform.types import JsonStr


@dataclass(frozen=True, slots=True)
class IntegrationMessage:
    message_id: str
    correlation_id: str
    causation_id: str
    occurred_at: datetime
    aggregate_id: str
    aggregate_name: str
    schema_version: int
    recipient_aggregate_id: str
    recipient_aggregate_name: str
    state_data: JsonStr

    def __post_init__(self) -> None:
        if (self.recipient_aggregate_id is None) != (self.recipient_aggregate_name is None):
            raise DomainError(
                "recipient_aggregate_id and recipient_aggregate_name must both be set or both be None"
            )
