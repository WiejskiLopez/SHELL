"""InboxProcessorBase — shared claim→process→ack lifecycle for inbox processors.

Event, message and command inbox processors implement the same operational
semantics, so the full lifecycle lives once in this base:

  Transaction A (claim):  ``InboxClaimService`` claims records, marks them
                          ``PROCESSING`` with a lease and commits — no DB lock
                          is held across the handler.
  Transaction B (ack):    each claimed record is deserialized and dispatched,
                          then acknowledged (``PROCESSED``) or scheduled for
                          retry / moved to DLQ with a conditional UPDATE keyed
                          by ``id + claimed_by``.

Subclasses provide only the type-specific parts: deserialization, dispatch and
the causation value used to seed the tracing context.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Protocol, cast

from sqlalchemy import func, select, update

from shell.platform.domain.value_objects.inbox_status import InboxStatus
from shell.platform.infrastructure.context import (
    DeliverySessionScope,
    causation_id_var,
    correlation_id_var,
    reset_session_scope,
    set_session_scope,
)
from shell.platform.infrastructure.messaging.inbox.envelope_validator import (
    UNSUPPORTED_SCHEMA_VERSION,
    EnvelopeValidator,
)
from shell.platform.infrastructure.messaging.inbox.inbox_batch_result import (
    InboxBatchResult,
)
from shell.platform.infrastructure.messaging.inbox.inbox_claim_service import (
    InboxClaimService,
    InboxStateModel,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.engine import CursorResult
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.application.ports.technical_id_generator import TechnicalIdGenerator
    from shell.platform.infrastructure.messaging.inbox.envelope_validator import (
        EnvelopeValidationPolicy,
    )

logger = logging.getLogger(__name__)


class _ClaimedInboxRow(Protocol):
    """Runtime instance shape of a claimed inbox row (read access)."""

    id: str
    correlation_id: str
    causation_id: str
    retry_count: int
    schema_version: int


class InboxProcessorBase:
    """Base class implementing the shared inbox processing lifecycle."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        inbox_model: type[InboxStateModel],
        batch_size: int = 100,
        max_retries: int = 3,
        retry_backoff_seconds: int = 30,
        max_retry_backoff_seconds: int = 3600,
        retry_jitter_seconds: float = 0.0,
        lease_duration_seconds: int = 60,
        worker_id: str | None = None,
        max_concurrency: int = 1,
        envelope_validator: EnvelopeValidator | None = None,
        envelope_policy: EnvelopeValidationPolicy | None = None,
        heartbeat_interval_seconds: float = 0.0,
        max_batch_time_seconds: float = 0.0,
        id_generator: TechnicalIdGenerator | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._inbox_model = inbox_model
        self._batch_size = batch_size
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds
        self._max_retry_backoff_seconds = max_retry_backoff_seconds
        self._retry_jitter_seconds = retry_jitter_seconds
        self._lease_duration_seconds = lease_duration_seconds
        self._heartbeat_interval_seconds = heartbeat_interval_seconds
        self._max_batch_time_seconds = max_batch_time_seconds
        from shell.platform.infrastructure.identity.uuid_technical_id_generator import (
            UuidTechnicalIdGenerator,
        )

        self._id_generator = id_generator or UuidTechnicalIdGenerator()
        self._worker_id = worker_id or f"inbox-worker-{self._id_generator.new_id()}"
        self._max_concurrency = max(max_concurrency, 1)
        self._envelope_validator = envelope_validator or EnvelopeValidator(envelope_policy)

        self._claim_service = InboxClaimService(
            session_factory,
            inbox_model,
            worker_id=self._worker_id,
            lease_duration_seconds=lease_duration_seconds,
            batch_size=batch_size,
        )

    # ------------------------------------------------------------------
    # Overridden by subclasses
    # ------------------------------------------------------------------

    def _deserialize(self, row: _ClaimedInboxRow) -> object | None:
        raise NotImplementedError

    async def _dispatch(self, domain_object: object) -> None:
        raise NotImplementedError

    def _causation_value(self, domain_object: object, row: _ClaimedInboxRow) -> str:
        raise NotImplementedError

    def _message_name(self, row: _ClaimedInboxRow) -> str:
        raise NotImplementedError

    def _delivery_id(self, row: _ClaimedInboxRow) -> str:
        """Return the logical delivery id (``event_id``/``command_id``)."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def run_once(self) -> InboxBatchResult:
        started = time.monotonic()
        if self._heartbeat_interval_seconds > 0:
            claimed = await self._claim_service.claim_batch()
        else:
            # Without a heartbeat the worker cannot renew the lease during a long
            # handler, so a batch is capped at one record (ref2.md §4.2).
            claimed = await self._claim_service.claim_batch(limit=1)

        if self._max_concurrency > 1:
            outcomes = await self._process_batch_concurrently(claimed)
        else:
            outcomes = []
            for row in claimed:
                if (
                    self._max_batch_time_seconds > 0
                    and (time.monotonic() - started) >= self._max_batch_time_seconds
                ):
                    logger.warning(
                        "batch time budget exceeded (max_batch_time=%s); "
                        "leaving %s claimed records to lease expiry",
                        self._max_batch_time_seconds,
                        len(claimed) - len(outcomes),
                    )
                    break
                outcomes.append(await self._process_claimed_row(cast("_ClaimedInboxRow", row)))

        processed_count = outcomes.count("processed")
        retried_count = outcomes.count("retried")
        dead_lettered_count = outcomes.count("dead_lettered")
        failed_count = outcomes.count("failed")

        duration_ms = int((time.monotonic() - started) * 1000)
        return InboxBatchResult(
            claimed_count=len(claimed),
            processed_count=processed_count,
            retried_count=retried_count,
            dead_lettered_count=dead_lettered_count,
            failed_count=failed_count,
            duration_ms=duration_ms,
        )

    async def _process_batch_concurrently(self, claimed: Sequence[object]) -> list[str]:
        """Process claimed records in bounded parallel tasks.

        Each record runs in its own ``asyncio.Task`` with an isolated context,
        so ``correlation_id_var``/``causation_id_var`` set inside one record's
        processing never leak into another concurrently processed record.
        """
        semaphore = asyncio.Semaphore(self._max_concurrency)

        async def _run_one(row: object) -> str:
            async with semaphore:
                try:
                    return await self._process_claimed_row(cast("_ClaimedInboxRow", row))
                except Exception:
                    logger.exception("unexpected failure processing record")
                    return "failed"

        results = await asyncio.gather(
            *(_run_one(row) for row in claimed),
            return_exceptions=False,
        )
        return list(results)

    async def _process_claimed_row(self, row: _ClaimedInboxRow) -> str:
        envelope_error = self._envelope_validator.validate(
            delivery_id=self._delivery_id(row),
            message_name=self._message_name(row),
            schema_version=row.schema_version,
            payload=getattr(row, "payload", {}),
            correlation_id=row.correlation_id,
            causation_id=row.causation_id,
        )
        if envelope_error is not None:
            return await self._schedule_failure(
                row.id,
                error_code=envelope_error,
                error_message=f"Envelope invalid for type {self._message_name(row)}: {envelope_error}",
                current_retry_count=row.retry_count,
                immediate_dead_letter=envelope_error == UNSUPPORTED_SCHEMA_VERSION,
            )

        domain_object = self._deserialize(row)

        if domain_object is None:
            return await self._schedule_failure(
                row.id,
                error_code="DESERIALIZATION_ERROR",
                error_message=f"Deserialization failed for type: {self._message_name(row)}",
                current_retry_count=row.retry_count,
            )

        corr_token = correlation_id_var.set(row.correlation_id)
        caus_token = causation_id_var.set(self._causation_value(domain_object, row))
        try:
            return await self._process_in_transaction(domain_object, row)
        except Exception as exc:
            return await self._schedule_failure(
                row.id,
                error_code="HANDLER_ERROR",
                error_message=f"{type(exc).__name__}: {exc}",
                current_retry_count=row.retry_count,
            )
        finally:
            correlation_id_var.reset(corr_token)
            causation_id_var.reset(caus_token)

    async def _process_in_transaction(self, domain_object: object, row: _ClaimedInboxRow) -> str:
        """Run dispatch, outbox and inbox ack inside one processing transaction.

        The processor owns the session (published as the ambient scope); any
        handler-side unit of work entered while the scope is active reuses it
        and defers its commit. A single commit therefore persists the business
        change, the local outbox rows and the ``PROCESSED`` status atomically.
        """
        async with self._session_factory() as session:
            scope = DeliverySessionScope(session=session)
            scope_token = set_session_scope(scope)
            try:
                if self._heartbeat_interval_seconds > 0:
                    if not await self._renew_lease(row.id):
                        return "failed"
                    lease_ok = await self._dispatch_with_heartbeat(row.id, domain_object)
                    if not lease_ok:
                        return await self._schedule_failure(
                            row.id,
                            error_code="HANDLER_ERROR",
                            error_message="Lease lost during processing (heartbeat failed)",
                            current_retry_count=row.retry_count,
                        )
                else:
                    await self._dispatch(domain_object)

                if scope.rolled_back:
                    return await self._schedule_failure(
                        row.id,
                        error_code="HANDLER_ERROR",
                        error_message="Handler rolled back its unit of work",
                        current_retry_count=row.retry_count,
                    )

                acknowledged = await self._acknowledge_in_session(session, row.id)
                if not acknowledged:
                    await session.rollback()
                    return "failed"
                await session.commit()
                return "processed"
            finally:
                reset_session_scope(scope_token)

    async def _acknowledge_in_session(self, session: AsyncSession, inbox_id: str) -> bool:
        now = await self._database_now(session)
        result = await session.execute(
            update(self._inbox_model)
            .where(
                self._inbox_model.id == inbox_id,
                self._inbox_model.status == InboxStatus.PROCESSING.value,
                self._inbox_model.claimed_by == self._worker_id,
            )
            .values(
                status=InboxStatus.PROCESSED.value,
                processed_at=now,
                lease_until=None,
                claimed_by=None,
                retry_count=0,
                last_attempted_at=None,
                error_code=None,
                error_message=None,
            )
        )
        return cast("CursorResult[object]", result).rowcount > 0

    async def _renew_lease(self, inbox_id: str) -> bool:
        """Conditionally extend the lease in its own short transaction.

        Zero affected rows means the record no longer belongs to this worker
        (reclaimed / processed elsewhere). A DB error during renewal also counts
        as a lost lease (ref4.md Krok 2): we cannot confirm ownership, so the
        caller must stop processing and must not acknowledge — ownership is
        confirmed again on the next successful renewal.
        """
        try:
            async with self._session_factory() as session:
                now = await self._database_now(session)
                result = await session.execute(
                    update(self._inbox_model)
                    .where(
                        self._inbox_model.id == inbox_id,
                        self._inbox_model.status == InboxStatus.PROCESSING.value,
                        self._inbox_model.claimed_by == self._worker_id,
                    )
                    .values(lease_until=now + timedelta(seconds=self._lease_duration_seconds))
                )
                await session.commit()
                return cast("CursorResult[object]", result).rowcount > 0
        except Exception:
            logger.exception("lease renewal failed for %s; treating lease as lost", inbox_id)
            return False

    async def _dispatch_with_heartbeat(
        self,
        inbox_id: str,
        domain_object: object,
    ) -> bool:
        """Dispatch while a background task renews the lease every interval.

        Returns ``False`` when the lease was lost (another worker reclaimed the
        record), so the caller must not acknowledge.
        """
        stop_event = asyncio.Event()
        lease_ok = {"value": True}
        heartbeat = asyncio.create_task(self._heartbeat_loop(inbox_id, stop_event, lease_ok))
        dispatch = asyncio.create_task(self._dispatch(domain_object))
        try:
            done, _ = await asyncio.wait(
                {dispatch, heartbeat},
                return_when=asyncio.FIRST_COMPLETED,
            )
            if heartbeat in done and not lease_ok["value"]:
                dispatch.cancel()
                with suppress(asyncio.CancelledError):
                    await dispatch
                return False
            await dispatch
        finally:
            stop_event.set()
            with suppress(asyncio.CancelledError):
                await heartbeat
        return lease_ok["value"]

    async def _heartbeat_loop(
        self,
        inbox_id: str,
        stop_event: asyncio.Event,
        lease_ok: dict[str, bool],
    ) -> None:
        while not stop_event.is_set():
            await asyncio.sleep(self._heartbeat_interval_seconds)
            if stop_event.is_set():
                return
            renewed = await self._renew_lease(inbox_id)
            if not renewed:
                lease_ok["value"] = False
                return

    async def _schedule_failure(
        self,
        inbox_id: str,
        *,
        error_code: str,
        error_message: str,
        current_retry_count: int,
        immediate_dead_letter: bool = False,
    ) -> str:
        next_retry_count = current_retry_count + 1
        dead_letter = immediate_dead_letter or next_retry_count >= self._max_retries

        async with self._session_factory() as session:
            now = await self._database_now(session)
            values: dict[str, object] = {
                "retry_count": next_retry_count,
                "last_attempted_at": now,
                "lease_until": None,
                "claimed_by": None,
                "error_code": error_code,
                "error_message": error_message,
            }
            if dead_letter:
                values["status"] = InboxStatus.DEAD_LETTER.value
                values["failed_at"] = now
                logger.critical(
                    "%s exceeded max_retries=%s — DLQ",
                    inbox_id,
                    self._max_retries,
                )
            else:
                values["status"] = InboxStatus.RETRY.value
                values["next_attempt_at"] = now + self._backoff(next_retry_count)

            result = await session.execute(
                update(self._inbox_model)
                .where(
                    self._inbox_model.id == inbox_id,
                    self._inbox_model.status == InboxStatus.PROCESSING.value,
                    self._inbox_model.claimed_by == self._worker_id,
                )
                .values(**values)
            )
            await session.commit()

        if cast("CursorResult[object]", result).rowcount == 0:
            return "failed"
        return "dead_lettered" if dead_letter else "retried"

    def _backoff(self, retry_count: int) -> timedelta:
        delay = min(
            self._max_retry_backoff_seconds,
            self._retry_backoff_seconds * (2 ** max(retry_count - 1, 0)),
        )
        jitter = random.uniform(0.0, self._retry_jitter_seconds)
        return timedelta(seconds=delay + jitter)

    async def _database_now(self, session: AsyncSession) -> datetime:
        raw = (await session.execute(select(func.current_timestamp()))).scalar_one()
        if isinstance(raw, str):
            raw = datetime.fromisoformat(raw)
        if raw.tzinfo is None:
            raw = raw.replace(tzinfo=UTC)
        return raw
