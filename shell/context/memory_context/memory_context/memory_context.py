"""memory_context.py
MemoryContext — long-term memory context: lessons learned, preferences, known patterns.

Slots:
    _lessons_learned         — list of lessons learned from previous processes
    _organization_preferences — list of organization-level preferences
    _known_patterns          — list of known architectural or process patterns
"""

from __future__ import annotations

from shell.context.memory_context.memory_context.internal._init_memory_context import _init_memory_context


class MemoryContext:
    """Long-term memory context.

    Slots:
        _lessons_learned          — list of lessons learned from previous processes
        _organization_preferences — list of organization-level preferences
        _known_patterns           — list of known architectural or process patterns
    """

    __slots__ = ("_lessons_learned", "_organization_preferences", "_known_patterns")

    def __init__(self) -> None:
        self._lessons_learned: list[str] = []
        self._organization_preferences: list[str] = []
        self._known_patterns: list[str] = []

    @property
    def lessons_learned_(self) -> list[str]:
        return self._lessons_learned

    @property
    def organization_preferences_(self) -> list[str]:
        return self._organization_preferences

    @property
    def known_patterns_(self) -> list[str]:
        return self._known_patterns

    def init_memory_context(self) -> None:
        _init_memory_context(self)
