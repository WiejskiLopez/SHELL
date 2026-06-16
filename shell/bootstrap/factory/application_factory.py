"""Główna fabryka aplikacji — inicjalizuje bazę, buduje kontener i wdraża szyny."""
from __future__ import annotations

from shell.bootstrap.container.core_container import CoreContainer
from shell.bootstrap.database_config.database_bootstrap import bootstrap_database
from shell.bootstrap.factory.bus_factory import wire_buses


class ApplicationFactory:
    """Buduje gotowy do użycia CoreContainer dla podanego adresu bazy danych."""

    def __init__(self, database_url: str, max_step: int = 0) -> None:
        self._database_url = database_url
        self._max_step = max_step

    async def build(self) -> CoreContainer:
        """Inicjalizuje schemat DB (jeśli potrzeba) i wdraża wszystkie komponenty."""
        await bootstrap_database(self._database_url)

        core_container = CoreContainer()
        core_container.config.db_url.from_value(self._database_url)
        core_container.config.max_step.from_value(self._max_step)

        wire_buses(core_container)

        return core_container
