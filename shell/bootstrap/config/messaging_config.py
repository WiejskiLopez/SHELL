"""Messaging infrastructure configuration."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MessagingConfig:
    """Configuration for outbox/inbox messaging infrastructure."""

    outbox_batch_size: int = 100
    inbox_batch_size: int = 100
    worker_poll_interval: float = 1.0      # seconds between polls when empty
    worker_backoff_factor: float = 2.0     # exponential backoff multiplier
    worker_max_backoff: float = 30.0       # max seconds to wait