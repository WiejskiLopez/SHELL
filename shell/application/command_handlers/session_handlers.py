"""OpenSessionHandler, CloseSessionHandler, AppendMessageHandler."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.entities.session import Session
from shell.domain.exceptions import DomainError
from shell.domain.value_objects.ids import CorrelationId, MessageId, SessionId

if TYPE_CHECKING:
    from shell.application.commands.commands import (
        AppendMessageCommand,
        CloseSessionCommand,
        OpenSessionCommand,
    )
    from shell.application.ports.ports import Clock, IdGenerator, UnitOfWork


class SessionNotFound(DomainError):
    pass


class OpenSessionHandler:
    def __init__(self, uow: UnitOfWork, clock: Clock, id_gen: IdGenerator) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen

    async def handle(self, cmd: OpenSessionCommand) -> SessionId:
        session_id = self._id_gen.new_session_id()
        session = Session.open(
            id_=session_id,
            goal=cmd.goal,
            now=self._clock.now(),
        )
        async with self._uow as uow:
            await uow.sessions.save(session)
            await uow.commit()
        return session_id


class CloseSessionHandler:
    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def handle(self, cmd: CloseSessionCommand) -> None:
        async with self._uow as uow:
            session = await uow.sessions.get_by_id(SessionId(cmd.session_id))
            if session is None:
                raise SessionNotFound(f"Session not found: {cmd.session_id}")
            session.close(self._clock.now())
            await uow.sessions.save(session)
            await uow.commit()


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
            msg_id = self._id_gen.new_message_id()
            session.append_message(
                msg_id=msg_id,
                correlation_id=CorrelationId(cmd.correlation_id),
                sender=cmd.sender,
                receiver=cmd.receiver,
                payload=dict(cmd.payload),
                now=self._clock.now(),
            )
            await uow.sessions.save(session)
            await uow.commit()
        return msg_id
