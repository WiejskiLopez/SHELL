from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.platform.value_objects.ids import CorrelationId
from shell.domain.execution.value_objects.ids import MessageId, SessionId

from shell.application.execution.command_handlers.session_handlers.session_not_found import SessionNotFound

if TYPE_CHECKING:
    from shell.application.platform.commands.commands import AppendMessageCommand
    from shell.application.platform.ports.ports import Clock, IdGenerator, UnitOfWork


class AppendMessageHandler:
    def __init__(self, uow: UnitOfWork, clock: Clock, id_gen: IdGenerator) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen

    async def handle(self, cmd: AppendMessageCommand) -> MessageId:
        async with self._uow as uow:
            session = await uow.sessions.get_by_id(SessionId(cmd.session_id))
            if session is None:
                raise SessionNotFound(f"Session not found: {cmd.session_id}")
            message_id = self._id_gen.new_message_id()
            session.append_message(
                msg_id=message_id,
                correlation_id=CorrelationId(cmd.correlation_id),
                sender=cmd.sender,
                receiver=cmd.receiver,
                payload=dict(cmd.payload),
                now=self._clock.now(),
            )
            await uow.sessions.save(session)
        return message_id
