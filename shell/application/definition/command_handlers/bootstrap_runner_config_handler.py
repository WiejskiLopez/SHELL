"""BootstrapRunnerConfigHandler."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.domain.definition.entities.runner_config import RunnerConfig
from shell.domain.platform.value_objects.hash import Hash

if TYPE_CHECKING:
    from shell.application.platform.commands.commands import BootstrapRunnerConfigCommand
    from shell.application.platform.ports.ports import Clock, IdGenerator, UnitOfWork


class BootstrapRunnerConfigHandler:
    def __init__(self, unit_of_work: UnitOfWork, clock: Clock, id_generator: IdGenerator) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator

    async def handle(self, bootstrap_runner_config_command: BootstrapRunnerConfigCommand) -> str:
        serialized = json.dumps(bootstrap_runner_config_command.body, sort_keys=True)
        config_hash = Hash.of(serialized)
        async with self._unit_of_work as unit_of_work:
            config = RunnerConfig.new(
                id_=self._id_generator.new_runner_config_id(),
                package_name=bootstrap_runner_config_command.package_name,
                kind=bootstrap_runner_config_command.kind,
                body=bootstrap_runner_config_command.body,
                config_hash=config_hash,
                now=self._clock.now(),
            )
            await unit_of_work.runner_config_repository.save(config)
        return config.id.value
