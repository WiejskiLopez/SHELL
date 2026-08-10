"""Main application factory — initializes the database, builds the container and wires buses."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.bootstrap.container.core_container import Container
from shell.platform.bootstrap.database_config.database_bootstrap import bootstrap_database
from shell.platform.bootstrap.factory.bus_factory import wire_buses

if TYPE_CHECKING:
    from shell.platform.infrastructure.configuration.shell_config import ShellConfig


class ApplicationFactory:
    """Buduje gotowy do użycia Container dla podanej konfiguracji."""

    def __init__(self, config: ShellConfig) -> None:
        self._config = config

    async def build(self) -> Container:
        """Inicjalizuje schemat DB (jeśli potrzeba) i wdraża wszystkie komponenty."""
        await bootstrap_database(self._config)

        container = Container(
            db_url=self._config.database_url,
            events_config={
                "outbox_batch_size": self._config.events.outbox_batch_size,
                "inbox_batch_size": self._config.events.inbox_batch_size,
                "worker_poll_interval": self._config.events.worker_poll_interval,
                "worker_backoff_factor": self._config.events.worker_backoff_factor,
                "worker_max_backoff": self._config.events.worker_max_backoff,
            },
        )
        container.config = self._config

        wire_buses(container)

        return container
