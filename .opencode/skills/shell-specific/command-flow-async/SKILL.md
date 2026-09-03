---
name: command-flow-async
description: Przepływ komendy/eventu ASYNCHRONICZNEGO (cross-BC) w SHELL — transactional outbox → Relay → RabbitMQ → inbox → Processor → (Event|Command)Bus → handler w session scope. Wszystkie klasy po drodze, dwie transakcje (claim + process/ack), idempotencja at-least-once i miejsca utraty/duplikacji. Używaj gdy projektujesz/refaktoryzujesz outbox/inbox, relay, transport, consumer, inbox processor, CommandDeliveryDispatcher, gdy analizujesz utratę lub duplikację wiadomości między BC. Uwaga: komendy delivery produkuje WYŁĄCZNIE warstwa process (saga); aplikacja ich nie dispatchuje.
---

# Command Flow ASYNCHRONICZNY w SHELL

## Charakterystyka

- Tryb: `outbox → Relay → RabbitMQ → inbox → Processor → (Event|Command)Bus → Handler` — fire-and-forget, eventual consistency.
- Gwarancja: **at-least-once** (nie exactly-once). Idempotencja: unique `(source_service, outbox_id)` na inboxie + `processed_delivery` przed dispatch.
- **Dwie transakcje** per rekord: A = claim/lease, B = przetwarzanie + ack (jeden commit efekt + outbox + ack).
- Dwa warianty tego samego szkieletu: **event** (`outbox_event`/`inbox_event`, routing `event.<name>`) i **komenda delivery** (`outbox_command`/`inbox_command`, routing `command.<name>`).

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
  port w `platform/process/saga/ports/command_delivery_dispatcher.py`;
- `SqlCommandDeliveryDispatcher.dispatch` (`messaging/command/sql_command_outbox_writer.py`)
  rozwiązuje kontrakt po `type(command)`, waliduje `target_service`, serializuje
  payload z pól dataclass i zapisuje do `outbox_command` **bez commita**
  (atomy z UoW handlera); wymaga aktywnego `DeliverySessionScope`;
- **odbiorca deserializuje do TEJ SAMEJ klasy** przez rejestr
  `command_name → class` (`serialization/command/deserializer.py`) i dispatchuje
  przez lokalny `CommandBus` (`command/processor/command_inbox_processor.py`).

**Producent komend delivery to wyłącznie warstwa `process/` (saga).** Aplikacja ich
nie dispatchuje — egzekwuje test `test_application_does_not_dispatch_delivery_commands`.

Pełny dokument (uwaga: może być nieaktualny nazewniczo): `command-flow-async.md` (root repo).

## Producent (nadawca)

```
Handler (sync lub process) → stage_events / CommandDeliveryDispatcher
  → commit (efekt + outbox atomowo)                   sql_alchemy_uow_base.py:142-190
  → OutboxToTransportRelay.run_once                   outbox_to_transport_relay.py:73-96
       SELECT published_at IS NULL FOR UPDATE SKIP LOCKED (PG, nie SQLite)
       deliver(envelope) dla każdego → published_at → commit
  → Rabbit*DeliveryTransport.deliver                  rabbit_*_delivery_transport.py:45-66
       exchange "shell.delivery" (topic), routing event.<name> / command.<name>
       PERSISTENT + publisher_confirms=True + mandatory=True + on_return_raises=True
```

Wariant komendy delivery (producent = **warstwa process / saga**; tor nadawczy **DOMKNIĘTY**):
- Port: `platform/process/saga/ports/command_delivery_dispatcher.py` (`CommandDeliveryDispatcher`).
- `SqlCommandDeliveryDispatcher` (`messaging/command/sql_command_outbox_writer.py`) — rozwiązuje `CommandContract`, waliduje `target_service`, `writer.append(scope.session, ...)` **bez commita** (atomy z UoW handlera); wymaga aktywnego `DeliverySessionScope`.
- `SqlCommandOutboxWriter.append` — nigdy nie commit; `StandaloneSqlCommandOutboxWriter` — własny commit, tylko poza UoW.
- `CommandOutboxToTransportRelay` (`command_transport/outbox_to_transport_relay.py`).
- Worker relaya komend wpięty w `run_delivery_workers(command_outbox_relay=...)` — zwalidowane na Rabbit.

## Konsument (odbiorca)

```
RabbitInboxConsumer._on_message → decode → insert inbox + commit → ack
  rabbit_*_inbox_consumer.py:74-118
  (pg_insert on_conflict_do_nothing + UniqueConstraint(source_service,outbox_id))
PollingWorker.run → task.run_once()                   polling_worker.py:62-113
  run_delivery_workers (event_worker.py:18-63) startuje consumerów + workery + outbox_relay
InboxClaimService.claim_batch (TRANSKACJA A)           inbox_claim_service.py:72-119
  SELECT status IN(PENDING,RETRY) AND next_attempt_at<=now
       OR status=PROCESSING AND lease_until<now
       FOR UPDATE SKIP LOCKED → PROCESSING + claimed_by + lease_until → commit
InboxProcessorBase._process_claimed_row                 inbox_processor_base.py:218-259
  EnvelopeValidator.validate → _deserialize → correlation_id_var/causation_id_var
  błąd → _schedule_failure (RETRY/DLQ, :416-471; max_retries=3, backoff)
  → _process_in_transaction (TRANSKACJA B)              :261-314
       DeliverySessionScope(session) → set_session_scope (session_scope.py:26-49)
       _is_duplicate (ProcessedDeliveryStore, :316-319)
       dispatch: EventBus.publish / CommandBus.dispatch
                 (event/processor/event_inbox_processor.py:105-106,
                  command/processor/command_inbox_processor.py:102-103)
       handler UoW deferred (wspólna sesja procesora, commit=flush)
       ack warunkowy UPDATE id+status=PROCESSING+claimed_by → PROCESSED (:321-341)
       session.commit() = efekt + lokalny outbox + PROCESSED (jedna transakcja)
       rowcount=0 → rollback → "failed" (lease zgubiony)
```

Modele: `event_delivery.py:26-68`, `command_delivery.py:26-75`, `InboxStateMixin` (`mixins/inbox_state.py:35-69`).

## Granice transakcji

- Producent: 1 transakcja — efekt + outbox (albo deferred w procesorze).
- Claim (A): krótka transakcja — PROCESSING + claimed_by + lease_until, bez zamka na czas handlera.
- Process (B): 1 transakcja — efekt + lokalny outbox + ack PROCESSED.
- Idempotencja: unique `(source_service, outbox_id)` na insert + `processed_delivery` przed dispatch (atomowo z efektem) + ack warunkowy po `id+status+claimed_by`.

## Punkty krytyczne (utrata / duplikaty)

1. **UTRATA (hard)**: `RabbitInboxConsumer` przy błędzie dekodowania robi `reject(requeue=False)` — wiadomość ginie bez DLQ (brak `x-dead-letter-exchange`). `rabbit_*_inbox_consumer.py:77-80`. → dodaj DLQ albo poison-store przed reject.
2. **~UTRATA (cicha)~ — ROZWIĄZANE**: pierwotnie tor nadawczy komend delivery był otwarty
   (brak producenta i relaya w `run_delivery_workers`); obecnie `CommandOutboxToTransportRelay`
   jest podłączony w 6 BC (`command_outbox_relay=...`) i zwalidowany na Rabbit. Producentem
   komend delivery jest wyłącznie warstwa process (saga).
3. **DUPLIKATY z relay**: `FOR UPDATE` trzymane przez wywołanie sieciowe brokera (`outbox_to_transport_relay.py:74-95`); częściowy błąd partii / crash między publish a commit → już-opublikowane wiersze publikowane ponownie. Łagodzone dedupem u konsumenta.
4. **Routing szeroki**: bindingi `event.#` / `command.#` (`rabbit_*_inbox_consumer.py:52`) — każdy BC odbiera wszystko; registry oparte o `__name__` klasy (`command_registry.py:19-38`) → ryzyko kolizji wire-name.
5. **Relay bez retry-state**: `outbox_event/command` nie mają `attempt_count/next_attempt_at/last_error` — zatruty wiersz blokuje partię, brak DLQ producenta.

Bezpieczne ogniwa: deferred UoW + `DeliverySessionScope` (jeden commit), dedup insert (unique source+outbox), dedup przed dispatch (`processed_delivery`), lease/claim/reclaim z warunkowym ack, publisher confirms + mandatory, RETRY/DLQ inbox z backoffem.

## Rekomendacje (minimum)

1. DLQ/dead-letter dla consumerów (poison zamiast `reject(requeue=False)`).
2. **ZROBIONE**: command relay jako osobny worker + port `CommandDeliveryDispatcher`; producentem jest wyłącznie warstwa process (saga), aplikacja nie dispatchuje komend delivery (test reguły).
3. Relay: krótka transakcja claim → publish poza transakcją → warunkowy `mark published`.
4. Retry state + DLQ na outboxie; routing `command.<target>.<name>`; stabilny wire-name zamiast `__name__`.

## Kluczowe pliki

- `platform/infrastructure/messaging/{event,command}_transport/{outbox_to_transport_relay,rabbit/rabbit_*_delivery_transport,rabbit/rabbit_*_inbox_consumer}.py`
- `platform/infrastructure/messaging/inbox/{inbox_claim_service,inbox_processor_base,processed_delivery_store,envelope_validator}.py`
- `platform/infrastructure/messaging/{event,command}/processor/{event,command}_inbox_processor.py`
- `platform/infrastructure/messaging/command/sql_command_outbox_writer.py`
- `platform/infrastructure/messaging/polling_worker.py`, `platform/infrastructure/messaging/event/event_worker.py`
- `platform/application/context/session_scope.py`
- `platform/infrastructure/persistence/sql/models/{event_delivery,command_delivery,mixins/inbox_state}.py`
- `bootstrap/<bc>/main.py` (wiring — command relay podłączony w 6 BC: execution, ingestion, project, scheduling, session, user)
