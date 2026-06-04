from __future__ import annotations

from typing import TYPE_CHECKING

from shell.bus.bus_schema.internal._apply_bus_schema import _apply_bus_schema

if TYPE_CHECKING:
    from shell.bus.message_bus.message_bus import MessageBus
    from shell.memory.sql_driver.sql_driver import SqlDriver


def _init_message_bus(bus: MessageBus, driver: SqlDriver) -> None:
    bus._driver = driver
    _apply_bus_schema(driver)
