"""Integration Event base class — cross-BC contract.

All integration events in the system inherit from this base class,
which defines the standard envelope fields including tracing context.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class IntegrationEvent:
    event_id: str
    correlation_id: str
    causation_id: str
    occurred_at: datetime
    aggregate_id: str
    aggregate_name: str
    schema_version: int
