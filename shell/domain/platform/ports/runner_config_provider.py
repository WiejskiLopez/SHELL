from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.definition.entities.runner_config import RunnerConfig
    from shell.domain.definition.value_objects.ids import RunnerConfigId


class RunnerConfigProvider(Protocol):
    def get_runner_config(self, id: RunnerConfigId) -> RunnerConfig: ...
