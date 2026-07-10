from __future__ import annotations

from typing import Protocol


class EventsConfigProtocol(Protocol):
    outbox_batch_size: int
    inbox_batch_size: int
    worker_poll_interval: float
    worker_backoff_factor: float
    worker_max_backoff: float


class AppConfig(Protocol):
    profile: str
    database_url: str
    max_step: int
    max_parallel: int
    log_level: str
    seed_dev_data: bool
    reset_db: bool
    events: EventsConfigProtocol
