"""BootstrapRunnerConfigHandler."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.entities.runner_config import RunnerConfig

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import BootstrapRunnerConfigCommand
    from shell_ddd.application.ports.ports import Clock, IdGenerator, UnitOfWork


class BootstrapRunnerConfigHandler:
    def __init__(self, uow: UnitOfWork, clock: Clock, id_gen: IdGenerator) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen

    async def handle(self, cmd: BootstrapRunnerConfigCommand) -> str:
        async with self._uow as uow:
            config = RunnerConfig.new(
                id_=self._id_gen.new_runner_config_id(),
                package_name=cmd.package_name,
                kind=cmd.kind,
                body=cmd.body,
                now=self._clock.now(),
            )
            await uow.runner_configs.save(config)
            await uow.commit()
        return config.id.value
