"""SavePromptHandler."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.entities.prompt import Prompt

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import SavePromptCommand
    from shell_ddd.application.ports.ports import Clock, IdGenerator, UnitOfWork


class SavePromptHandler:
    def __init__(self, uow: UnitOfWork, clock: Clock, id_gen: IdGenerator) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen

    async def handle(self, cmd: SavePromptCommand) -> str:
        async with self._uow as uow:
            existing = await uow.prompts.get_current_by_name(cmd.name)
            if existing:
                existing.is_current = False
                await uow.prompts.save(existing)
            prompt = Prompt.new(
                id_=self._id_gen.new_prompt_id(),
                name=cmd.name,
                body=cmd.body,
                source_uri=cmd.source_uri,
                now=self._clock.now(),
            )
            await uow.prompts.save(prompt)
            await uow.commit()
        return prompt.id.value
