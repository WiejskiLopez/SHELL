from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.infrastructure.messaging.messaging.envelope import Envelope
from shell.infrastructure.messaging.persistence.sql.models.inbox_message import (
    InboxMessageModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.domain.messaging.aggregates.message_router.repositories.message_router_repository import (
        MessageRouterRepository,
    )
    from shell.platform.application.bus.message_bus import MessageBus


class MessageInboxProcessor:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        message_repository: MessageRouterRepository,
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
                envelope = Envelope.from_dict(dict(row.envelope))
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
