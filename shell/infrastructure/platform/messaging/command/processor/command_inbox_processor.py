from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from shell.infrastructure.platform.messaging.serialization.command_deserializer import (
    CommandDeserializer,
)
from shell.infrastructure.platform.persistence.sql.models.command.inbox_command import InboxCommandModel
from sqlalchemy import text

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.application.platform.bus.command_bus import CommandBus


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
                        SELECT id, command_type, occurred_at, payload
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

            now = datetime.now(timezone.utc)
            ids = []
            for row in rows:
                command = self._deserializer.deserialize(
                    command_type=row.command_type,
                    payload=row.payload,
                )
                if command is not None:
                    await self._command_bus.dispatch(command)
                ids.append(row.id)

            await session.execute(
                text("UPDATE inbox_command SET processed_at = :now WHERE id = ANY(:ids)"),
                {"now": now, "ids": ids},
            )
            await session.commit()
            return len(rows)
