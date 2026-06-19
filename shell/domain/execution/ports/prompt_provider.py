from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.definition.entities.prompt import Prompt
    from shell.domain.platform.value_objects.ids import PromptId


class PromptProvider(Protocol):
    def get_prompt(self, id: PromptId) -> Prompt: ...
