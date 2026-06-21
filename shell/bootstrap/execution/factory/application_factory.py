"""Główna fabryka aplikacji — inicjalizuje bazę, buduje kontener i wdraża szyny."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.bootstrap.platform.container.core_container import CoreContainer
from shell.bootstrap.platform.database_config.database_bootstrap import bootstrap_database
from shell.bootstrap.platform.factory.bus_factory import wire_buses

if TYPE_CHECKING:
    from shell.infrastructure.platform.configuration.shell_config import ShellConfig


class ApplicationFactory:
    """Buduje gotowy do użycia CoreContainer dla podanej konfiguracji."""

    def __init__(self, config: ShellConfig) -> None:
        self._config = config

    async def build(self) -> CoreContainer:
        """Inicjalizuje schemat DB (jeśli potrzeba) i wdraża wszystkie komponenty."""
        await bootstrap_database(self._config)

        core_container = CoreContainer()
        core_container.config.db_url.from_value(self._config.database_url)
        core_container.config.max_step.from_value(self._config.max_step)

        # Override events config from ShellConfig
        core_container.config.events.from_value(
            {
                "outbox_batch_size": self._config.events.outbox_batch_size,
                "inbox_batch_size": self._config.events.inbox_batch_size,
                "worker_poll_interval": self._config.events.worker_poll_interval,
                "worker_backoff_factor": self._config.events.worker_backoff_factor,
                "worker_max_backoff": self._config.events.worker_max_backoff,
            }
        )

        wire_buses(core_container)

        return core_container
