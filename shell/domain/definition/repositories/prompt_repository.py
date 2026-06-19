from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.definition.entities.prompt import Prompt
    from shell.domain.platform.value_objects.ids import PromptId


class PromptRepository(Protocol):
    async def get_by_id(self, prompt_id: PromptId) -> Prompt | None: ...
    async def get_current_by_name(self, name: str) -> Prompt | None: ...
    async def save(self, prompt: Prompt) -> None: ...
