from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell.infrastructure.platform.context import (
    causation_id_var,
    correlation_id_var,
)
from shell.infrastructure.platform.messaging.serialization.command_deserializer import (
    CommandDeserializer,
)
from sqlalchemy import text

if TYPE_CHECKING:
    from shell.application.platform.bus.command_bus import CommandBus
    from sqlalchemy.ext.asyncio import async_sessionmaker


class CommandInboxProcessor:
    def __init__(
        self,
        session_factory: async_sessionmaker,
        command_bus: CommandBus,
        batch_size: int = 100,
    ) -> None:
        self._session_factory = session_factory
        self._command_bus = command_bus
        self._batch_size = batch_size
        self._deserializer = CommandDeserializer()

    async def run_once(self) -> int:
        async with self._session_factory() as session:
            rows = (
                await session.execute(
                    text("""
                        SELECT id, command_type, occurred_at, payload, correlation_id, causation_id
                        FROM inbox_command
                        WHERE processed_at IS NULL
                        LIMIT :limit
                        FOR UPDATE SKIP LOCKED
                    """),
                    {"limit": self._batch_size},
                )
            ).all()

            if not rows:
                return 0

            now = datetime.now(UTC)
            ids = []
            for row in rows:
                command = self._deserializer.deserialize(
                    command_type=row.command_type,
                    payload=row.payload,
                )
                if command is not None:
                    corr_token = correlation_id_var.set(row.correlation_id)
                    caus_token = causation_id_var.set("")
                    try:
                        await self._command_bus.dispatch(command)
                    finally:
                        correlation_id_var.reset(corr_token)
                        causation_id_var.reset(caus_token)
                ids.append(row.id)

            await session.execute(
                text("UPDATE inbox_command SET processed_at = :now WHERE id = ANY(:ids)"),
                {"now": now, "ids": ids},
            )
            await session.commit()
            return len(rows)
