---
name: command-flow-async
description: Przepływ komendy/eventu ASYNCHRONICZNEGO (cross-BC) w SHELL — transactional outbox → Relay → RabbitMQ → inbox → Processor → (Event|Command)Bus → handler w session scope. Wszystkie klasy po drodze, dwie transakcje (claim + process/ack), idempotencja at-least-once i miejsca utraty/duplikacji. Używaj gdy projektujesz/refaktoryzujesz outbox/inbox, relay, transport, consumer, inbox processor, CommandDeliveryDispatcher, gdy analizujesz utratę lub duplikację wiadomości między BC. Uwaga: komendy delivery produkuje WYŁĄCZNIE warstwa process (saga); aplikacja ich nie dispatchuje.
---

# Command Flow ASYNCHRONICZNY w SHELL

## Charakterystyka

- Tryb: `outbox → Relay → RabbitMQ → inbox → Processor → (Event|Command)Bus → Handler` — fire-and-forget, eventual consistency.
- Gwarancja: **at-least-once** (nie exactly-once). Idempotencja: unikalny `(source_service, event_id|command_id)` na inboxie (`on_conflict_do_nothing` przy insert) + warunkowy ack po `id+status+claimed_by`.
- **Dwie transakcje** per rekord: A = claim/lease, B = przetwarzanie + ack (jeden commit efekt + outbox + ack).
- Dwa warianty tego samego szkieletu: **event** (`event_outbox`/`event_inbox`, routing `event.<contract_type>`) i **komenda delivery** (`command_outbox`/`command_inbox`, routing `command.<destination_service>.<contract_type>`).

## Obiekt komendy delivery — NIE jest osobnym typem

**W SHELL nie ma odrębnego typu „komendy async/ProcessCommand".** Komenda to jedna,
ta sama `@dataclass(frozen=True, slots=True)` opisująca intencję biznesową (np.
`CreateProjectCommand`). Asynchroniczność/synchroniczność **nie jest właściwością
typu, tylko sposobu dostarczenia**:

- **Komenda lokalna** — zarejestrowana w `CommandBus` (handler w tym samym BC, jedna transakcja).
- **Komenda delivery** — ma dodatkowo **`CommandContract`** = `command_name`
  (stabilny wire-name), `command_class`, `target_service`, `schema_version`
  (`platform/application/contracts/command_contract.py:13-19`). Dostarczana
  `outbox→Relay→broker→inbox`, at-least-once.

Różnicę wnosi **port dispatchera, nie klasa**:
- `CommandDeliveryDispatcher.dispatch(command: Command, *, target_service)` —
  port w bibliotece `saga-orchestration` (`process/saga/ports/command_delivery_dispatcher.py`);
- `SqlCommandDeliveryDispatcher.dispatch` (`messaging/command/sql_command_outbox_writer.py`)
  rozwiązuje kontrakt po `type(command)`, waliduje `target_service`, serializuje
  payload z pól dataclass i zapisuje do `command_outbox` **bez commita**
  (atomy z UoW handlera); wymaga aktywnego `DeliverySessionScope`;
- **odbiorca deserializuje do TEJ SAMEJ klasy** przez rejestr
  `command_name → class` (`serialization/command/deserializer.py`) i dispatchuje
  przez lokalny `CommandBus` (`command/command_inbox_processor.py`).

**Producent komend delivery to wyłącznie warstwa `process/` (saga).** Aplikacja ich
nie dispatchuje — egzekwuje test `test_application_does_not_dispatch_delivery_commands`.

Mechanizm sagi (manager, porty, repozytoria, worker timeoutów) żyje w bibliotece
`saga-orchestration` (`packaging/saga-orchestration`), a capability jest opt-in per
serwis — zob. `shell/project_service/process/` (pilotażowa saga) i
`packaging/saga-orchestration/`.

## Producent (nadawca)

```
Handler (sync lub process) → stage_events / CommandDeliveryDispatcher
  → commit (efekt + outbox atomowo)                   sql_alchemy_uow_base.py:142-190
  → EventOutboxRelay / CommandOutboxRelay.run_once     event|command_outbox_relay.py
       (cykl w OutboxRelayBase: SELECT published_at IS NULL FOR UPDATE SKIP LOCKED (PG, nie SQLite))
       deliver(envelope) dla każdego → published_at → commit
  → Rabbit*DeliveryTransport.deliver                  rabbit_*_delivery_transport.py:45-66
       exchange "shell.delivery" (topic), routing event.<contract_type> / command.<destination_service>.<contract_type>
       PERSISTENT + publisher_confirms=True + mandatory=True + on_return_raises=True
```

Wariant komendy delivery (producent = **warstwa process / saga**; tor nadawczy **DOMKNIĘTY**):
- Port: `process/saga/ports/command_delivery_dispatcher.py` (`CommandDeliveryDispatcher`) w `saga-orchestration`.
- `SqlCommandDeliveryDispatcher` (`messaging/command/sql_command_outbox_writer.py`) — rozwiązuje `CommandContract`, waliduje `target_service`, `writer.append(scope.session, ...)` **bez commita** (atomy z UoW handlera); wymaga aktywnego `DeliverySessionScope`.
- `SqlCommandOutboxWriter.append` — nigdy nie commituje (atomy z UoW handlera).
- `CommandOutboxRelay` (`messaging/command/command_outbox_relay.py`, baza `OutboxRelayBase` w `messaging/delivery/`).
- Worker relaya komend wpięty w `run_delivery_workers(command_outbox_relay=...)` — zwalidowane na Rabbit.

## Konsument (odbiorca)

```
EventInboxConsumer/CommandInboxConsumer._on_message → decode → insert inbox + commit → ack
  event/command_inbox_consumer.py:75-118 (event) / 73-112 (command)
  (pg_insert on_conflict_do_nothing + UniqueConstraint(source_service,event_id/command_id))
PollingWorker.run → task.run_once()                   polling_worker.py:62-113
  run_delivery_workers (event_worker.py:18-63) startuje consumerów + workery + outbox_relay
InboxClaimService.claim_batch (TRANSKACJA A)           inbox_claim_service.py:72-119
  SELECT status IN(PENDING,RETRY) AND next_attempt_at<=now
       OR status=PROCESSING AND lease_until<now
       FOR UPDATE SKIP LOCKED → PROCESSING + claimed_by + lease_until → commit
InboxProcessorBase._process_claimed_row                 inbox_processor_base.py:211-252
  EnvelopeValidator.validate → _deserialize → correlation_id_var/causation_id_var
  błąd → _schedule_failure (RETRY/DLQ, :392-439; max_retries=3, backoff)
  → _process_in_transaction (TRANSKACJA B)              :254-295
       DeliverySessionScope(session) → set_session_scope (session_scope.py:26-49)
       dispatch: EventBus.publish / CommandBus.dispatch
                 (event/event_inbox_processor.py:100-101,
                  command/command_inbox_processor.py:99-100)
       handler UoW deferred (wspólna sesja procesora, commit=flush)
       ack warunkowy UPDATE id+status=PROCESSING+claimed_by → PROCESSED (:297-317)
       session.commit() = efekt + lokalny outbox + PROCESSED (jedna transakcja)
       rowcount=0 → rollback → "failed" (lease zgubiony)
```

Modele: `event_delivery.py:26-68`, `command_delivery.py:26-75`, `InboxStateMixin` (`mixins/inbox_state.py:35-69`).

## Granice transakcji

- Producent: 1 transakcja — efekt + outbox (albo deferred w procesorze).
- Claim (A): krótka transakcja — PROCESSING + claimed_by + lease_until, bez zamka na czas handlera.
- Process (B): 1 transakcja — efekt + lokalny outbox + ack PROCESSED.
- Idempotencja: unique `(source_service, event_id|command_id)` na insert (`on_conflict_do_nothing`) + warunkowy ack po `id+status+claimed_by`.

## Punkty krytyczne (utrata / duplikaty)

1. **UTRATA (hard)**: `EventInboxConsumer`/`CommandInboxConsumer` przy błędzie dekodowania robią `reject(requeue=False)` — wiadomość ginie bez DLQ (brak `x-dead-letter-exchange`). `event|command_inbox_consumer.py:77-80`. → dodaj DLQ albo poison-store przed reject.
2. **~UTRATA (cicha)~ — ROZWIĄZANE**: pierwotnie tor nadawczy komend delivery był otwarty
   (brak producenta i relaya w `run_delivery_workers`); obecnie `CommandOutboxRelay`
   jest podłączony w 6 BC (`command_outbox_relay=...`) i zwalidowany na Rabbit. Producentem
   komend delivery jest wyłącznie warstwa process (saga).
3. **DUPLIKATY z relay**: `FOR UPDATE` trzymane przez wywołanie sieciowe brokera
   (`messaging/event|command/...outbox_relay.py` — cykl w `OutboxRelayBase`); częściowy błąd
   partii / crash między publish a commit → już-opublikowane wiersze publikowane ponownie.
   Łagodzone dedupem u konsumenta.
4. **Routing szeroki**: event consumer binduje `event.#`, command consumer `command.<service>.#` (`event_inbox_consumer.py:53`, `command_inbox_consumer.py:70`) — każdy BC odbiera wszystkie eventy; registry oparte o `__name__` klasy (`command_registry.py:19-38`) → ryzyko kolizji wire-name.
5. **Relay bez retry-state**: `event_outbox`/`command_outbox` nie mają `attempt_count/next_attempt_at/last_error` — zatruty wiersz blokuje partię, brak DLQ producenta.

Bezpieczne ogniwa: deferred UoW + `DeliverySessionScope` (jeden commit), dedup insert (unique source+event_id/command_id), lease/claim/reclaim z warunkowym ack, publisher confirms + mandatory, RETRY/DLQ inbox z backoffem.

## Rekomendacje (minimum)

1. DLQ/dead-letter dla consumerów (poison zamiast `reject(requeue=False)`).
2. **ZROBIONE**: command relay jako osobny worker + port `CommandDeliveryDispatcher`; producentem jest wyłącznie warstwa process (saga), aplikacja nie dispatchuje komend delivery (test reguły).
3. Relay: krótka transakcja claim → publish poza transakcją → warunkowy `mark published`.
4. Retry state + DLQ na outboxie; routing `command.<target>.<name>`; stabilny wire-name zamiast `__name__`.

## Kluczowe pliki

- `platform/infrastructure/messaging/{event,command}/{event,command}_outbox_relay.py` + `platform/infrastructure/messaging/delivery/outbox_relay_base.py`
- `platform/infrastructure/messaging/{event,command}_transport/rabbit/rabbit_*_delivery_transport.py`, `platform/infrastructure/messaging/{event,command}/{event,command}_inbox_consumer.py`
- `platform/infrastructure/messaging/inbox/inbox_claim_service.py`, `platform/infrastructure/messaging/delivery/inbox_processor_base.py`, `platform/infrastructure/messaging/inbox/envelope_validator.py`
- `platform/infrastructure/messaging/{event,command}/{event,command}_inbox_processor.py`
- `platform/infrastructure/messaging/command/sql_command_outbox_writer.py`
- `platform/infrastructure/messaging/polling_worker.py`, `platform/infrastructure/messaging/event/event_worker.py`
- `platform/application/context/session_scope.py`
- `platform/infrastructure/persistence/sql/models/{event_delivery,command_delivery,mixins/inbox_state}.py`
- `bootstrap/<bc>/main.py` (wiring — command relay podłączony w 6 BC: execution, ingestion, project, scheduling, session, user)
