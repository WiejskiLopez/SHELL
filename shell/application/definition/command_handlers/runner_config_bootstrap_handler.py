"""RunnerConfigBootstrapHandler."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.domain.definition.entities.runner_config import RunnerConfig
from shell.domain.definition.repositories.runner_config_repository import RunnerConfigRepository
from shell.domain.definition.value_objects.ids import RunnerConfigId
from shell.domain.definition.value_objects.package_name import PackageName
from shell.domain.definition.value_objects.runner_body import RunnerBody
from shell.domain.definition.value_objects.runner_kind import RunnerKind
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.hash import Hash

if TYPE_CHECKING:
    from shell.application.definition.commands.config_commands import BootstrapRunnerConfigCommand
    from shell.application.platform.ports.ports import Clock, IdGenerator, UnitOfWork


class RunnerConfigBootstrapHandler:
    def __init__(self, unit_of_work: UnitOfWork, clock: Clock, id_generator: IdGenerator) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator

    async def handle(self, bootstrap_runner_config_command: BootstrapRunnerConfigCommand) -> str:
        serialized = json.dumps(bootstrap_runner_config_command.body, sort_keys=True)
        config_hash = Hash.of(serialized)
        async with self._unit_of_work as unit_of_work:
            config = RunnerConfig.new(
                id_=self._id_generator.new_id(RunnerConfigId),
                package_name=PackageName(bootstrap_runner_config_command.package_name),
                kind=RunnerKind(bootstrap_runner_config_command.kind),
                body=RunnerBody(bootstrap_runner_config_command.body),
                config_hash=config_hash,
                now=CreatedAt.from_datetime(self._clock.now()),
            )
            await unit_of_work.repository(RunnerConfigRepository).save(config)
        return config.id.value
