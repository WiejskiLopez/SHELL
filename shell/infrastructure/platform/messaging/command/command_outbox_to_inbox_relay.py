from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell.infrastructure.platform.persistence.sql.models.command.inbox_command import (
    InboxCommandModel,
)
from sqlalchemy import text

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class CommandOutboxToInboxRelay:
    def __init__(
        self,
        session_factory: async_sessionmaker,
        batch_size: int = 100,
    ) -> None:
        self._session_factory = session_factory
        self._batch_size = batch_size

    async def run_once(self) -> int:
        async with self._session_factory() as session:
            rows = (
                await session.execute(
                    text("""
                        SELECT id, command_type, occurred_at, payload, correlation_id, causation_id
                        FROM outbox_command
                        WHERE published_at IS NULL
                        LIMIT :limit
                        FOR UPDATE SKIP LOCKED
                    """),
                    {"limit": self._batch_size},
                )
            ).all()

            if not rows:
                return 0

            now = datetime.now(UTC)
            for row in rows:
                inbox = InboxCommandModel(
                    id=str(uuid.uuid4()),
                    command_type=row.command_type,
                    occurred_at=row.occurred_at,
                    payload=row.payload,
                    correlation_id=row.correlation_id,
                    causation_id=row.causation_id,
                    received_at=now,
                )
                session.add(inbox)

            ids = [r.id for r in rows]
            await session.execute(
                text("UPDATE outbox_command SET published_at = :now WHERE id = ANY(:ids)"),
                {"now": now, "ids": ids},
            )

            await session.commit()
            return len(rows)
