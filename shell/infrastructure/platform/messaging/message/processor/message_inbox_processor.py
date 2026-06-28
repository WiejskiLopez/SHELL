"""MessageInboxProcessor — consumes inbox_message rows and dispatches to MessageBus."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell.domain.platform.envelope import Envelope
from shell.infrastructure.platform.persistence.sql.models.message.inbox_message import InboxMessageModel
from sqlalchemy import select

if TYPE_CHECKING:
    from shell.application.platform.bus.message_bus import MessageBus
    from shell.domain.platform.aggregates.message.repositories.message_repository import MessageRepository
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class MessageInboxProcessor:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        message_repository: MessageRepository,
        message_bus: MessageBus,
        batch_size: int = 100,
    ) -> None:
        self._session_factory = session_factory
        self._message_repo = message_repository
        self._message_bus = message_bus
        self._batch_size = batch_size

        engine = getattr(session_factory, "bind", None)
        dialect_name: str = engine.dialect.name if engine is not None else "unknown"
        self._skip_locked: bool = dialect_name not in ("sqlite",)

    async def run_once(self) -> int:
        async with self._session_factory() as session:
            stmt = (
                select(InboxMessageModel)
                .where(InboxMessageModel.processed_at.is_(None))
                .order_by(InboxMessageModel.received_at)
                .limit(self._batch_size)
            )
            if self._skip_locked:
                stmt = stmt.with_for_update(skip_locked=True)

            rows = (await session.execute(stmt)).scalars().all()
            if not rows:
                return 0

            messages_to_dispatch = []

            for row in rows:
                envelope = Envelope.from_dict(dict(row.envelope or {}))
                message = await self._message_repo.get_by_id(envelope.message_id)  # type: ignore[arg-type]
                if message is not None:
                    messages_to_dispatch.append(message)
                else:
                    row.error = f"Message not found: {envelope.message_id}"
                row.processed_at = datetime.now(tz=UTC)

            await session.commit()

            if messages_to_dispatch:
                await self._message_bus.dispatch(messages_to_dispatch)

            return len(rows)
