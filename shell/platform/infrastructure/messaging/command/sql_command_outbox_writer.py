"""Command outbox writer and the CommandDeliveryDispatcher adapter.

The session-based writer appends to ``outbox_command`` on the active session and
never commits — the caller's unit of work owns the transaction (atomicity of the
domain change and the command delivery).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

from shell.platform.application.context.session_scope import get_session_scope
from shell.platform.application.contracts.command_contract import (
    CommandContract,
    command_contracts_by_class,
)
from shell.platform.infrastructure.context import (
    get_causation_id,
    get_or_create_correlation_id,
)
from shell.platform.infrastructure.serialization.payload.payload_object_serializer import (
    PayloadObjectSerializer,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.platform.application.ports.technical_id_generator import TechnicalIdGenerator
    from shell.platform.infrastructure.persistence.sql.models.command_delivery import (
        CommandDeliveryModels,
    )


class SqlCommandOutboxWriter:
    """Writes command deliveries on the given session — never commits."""

    def __init__(
        self,
        models: CommandDeliveryModels,
        source_service: str,
        id_generator: TechnicalIdGenerator | None = None,
    ) -> None:
        self._outbox_model = models.outbox
        self._source_service = source_service
        if id_generator is None:
            from shell.platform.infrastructure.identity.uuid_technical_id_generator import (
                UuidTechnicalIdGenerator,
            )

            id_generator = UuidTechnicalIdGenerator()
        self._id_generator = id_generator

    def append(
        self,
        session: AsyncSession,
        *,
        contract: CommandContract,
        payload: dict[str, object],
        command_id: str | None = None,
        issued_at: datetime | None = None,
    ) -> str:
        resolved_command_id = command_id or str(self._id_generator.new_id())
        session.add(
            self._outbox_model(
                id=str(self._id_generator.new_id()),
                command_id=resolved_command_id,
                command_name=contract.command_name,
                source_service=self._source_service,
                target_service=contract.target_service,
                schema_version=contract.schema_version,
                issued_at=issued_at or datetime.now(tz=UTC),
                payload=payload,
                correlation_id=get_or_create_correlation_id(),
                causation_id=get_causation_id(),
            )
        )
        return resolved_command_id


class SqlCommandDeliveryDispatcher:
    """CommandDeliveryDispatcher adapter: resolves the contract and appends on the
    active processing session without its own commit."""

    def __init__(
        self,
        commands: Mapping[str, CommandContract],
        writer: SqlCommandOutboxWriter,
    ) -> None:
        self._by_class = command_contracts_by_class(commands)
        self._writer = writer
        self._payload_serializer = PayloadObjectSerializer()

    async def dispatch(self, command: object, *, target_service: str) -> str:
        contract = self._by_class.get(type(command))
        if contract is None:
            raise ValueError(f"No command contract for {type(command).__name__}")
        if contract.target_service != target_service:
            raise ValueError(
                f"Command {contract.command_name!r} targets {contract.target_service}, "
                f"got {target_service!r}"
            )

        scope = get_session_scope()
        if scope is None or scope.session is None:
            raise RuntimeError(
                "SqlCommandDeliveryDispatcher requires an active unit-of-work session scope"
            )

        payload = self._payload_serializer.to_payload(command)

        # Tożsamość komendy nadana przy konstrukcji jest jedynym źródłem prawdy:
        # zachowujemy ją w outboxie (command_id kolumny = command_id obiektu),
        # zamiast generować nowy identyfikator na warstwie dostawy.
        command_id = cast("str | None", getattr(command, "command_id", None))
        return self._writer.append(
            scope.session,
            contract=contract,
            payload=payload,
            command_id=command_id,
        )
