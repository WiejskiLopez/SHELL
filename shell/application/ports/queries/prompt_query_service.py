from __future__ import annotations

from typing import Protocol

from shell.application.dto import PromptDto


class PromptQueryService(Protocol):
    """Port do pobierania treści promptów."""

    async def get_prompt(self, name: str) -> PromptDto | None: ...
