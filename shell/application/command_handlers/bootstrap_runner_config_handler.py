"""BootstrapRunnerConfigHandler."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.domain.entities.runner_config import RunnerConfig
from shell.domain.value_objects.hash import Hash

if TYPE_CHECKING:
    from shell.application.commands.commands import BootstrapRunnerConfigCommand
    from shell.application.ports.ports import Clock, IdGenerator, UnitOfWork


class BootstrapRunnerConfigHandler:
    def __init__(self, uow: UnitOfWork, clock: Clock, id_gen: IdGenerator) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen

    async def handle(self, cmd: BootstrapRunnerConfigCommand) -> str:
        serialized = json.dumps(cmd.body, sort_keys=True)
        config_hash = Hash.of(serialized)
        async with self._uow as uow:
            config = RunnerConfig.new(
                id_=self._id_gen.new_runner_config_id(),
                package_name=cmd.package_name,
                kind=cmd.kind,
                body=cmd.body,
                config_hash=config_hash,
                now=self._clock.now(),
            )
            await uow.runner_configs.save(config)
            await uow.commit()
        return config.id.value
