"""Events infrastructure configuration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EventsConfig:
    """Configuration for outbox/inbox event infrastructure."""

    outbox_batch_size: int = 100
    inbox_batch_size: int = 100
