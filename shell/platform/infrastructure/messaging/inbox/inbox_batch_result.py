"""InboxBatchResult — structured outcome of one inbox processing pass."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InboxBatchResult:
    claimed_count: int
    processed_count: int
    retried_count: int
    dead_lettered_count: int
    failed_count: int
    duration_ms: int
