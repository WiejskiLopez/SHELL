from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.repositories.prompt_repository import PromptRepository
from shell.domain.definition.value_objects.ids import PromptId

if TYPE_CHECKING:
    from shell.domain.definition.entities.prompt import Prompt


class InMemoryPromptRepository(PromptRepository):
    def __init__(self) -> None:
        self._store: dict[str, Prompt] = {}

    async def get_by_id(self, prompt_id: PromptId) -> Prompt | None:
        return self._store.get(prompt_id.value)

    async def get_current_by_name(self, name: str) -> Prompt | None:
        for prompt in self._store.values():
            if prompt.name == name and prompt.is_current:
                return prompt
        return None

    async def save(self, prompt: Prompt) -> None:
        self._store[prompt.id.value] = prompt
