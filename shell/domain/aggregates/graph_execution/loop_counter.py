from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class LoopCounter:
    transition_id: str
    current_iteration: int = 0
    max_loop_count: int = 0

    @property
    def is_exhausted(self) -> bool:
        return self.max_loop_count > 0 and self.current_iteration >= self.max_loop_count

    def increment(self) -> int:
        self.current_iteration += 1
        return self.current_iteration
