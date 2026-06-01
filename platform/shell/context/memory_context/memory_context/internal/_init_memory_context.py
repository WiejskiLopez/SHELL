from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.context.memory_context.memory_context.memory_context import MemoryContext


def _init_memory_context(memory_context: MemoryContext) -> None:
    memory_context._lessons_learned = []
    memory_context._organization_preferences = []
    memory_context._known_patterns = []
