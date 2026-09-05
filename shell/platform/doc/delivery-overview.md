# Przepływ delivery end-to-end

## Cel / Co realizuje

Opisuje jedną ścieżkę przekazywania deliverable (event, command) między bounded contextami platformy SHELL: zapis w transakcyjnym outboxie, relay do transportu i brokera, zapis w inboxie, claim z lease, procesor oraz atomowy ack w konsumenckim BC. Wszystkie rodzaje korzystają z `EventOutboxRelay`/`CommandOutboxRelay` (na bazie `OutboxRelayBase`), kopert `EventDeliveryEnvelope`/`CommandDeliveryEnvelope`, `EnvelopeCodec` i odpowiedniego procesora inbox.

## Problem

Bounded contexts są od siebie niezależne (oddzielne bazy, procesy, cykle życia transakcji), a mimo to muszą wymieniać stan bez tracenia wiadomości. Bezpośrednie publikowanie do brokera w trakcie transakcji daje utratę wiadomości przy awarii między commitem a wysłaniem (dual write). Z drugiej strony konsument odbierający wiadomość at-least-once może ją przetworzyć dwukrotnie przy redelivery. Potrzebny jest mechanizm: trwałego zapisu deliverable atomowo ze stanem domeny (outbox), transportu, który nie gubi wiadomości, oraz konsumpcji z deduplikacją, identyfikowalnością (correlation/causation) i atomowym potwierdzeniem.

## Realizacja techniczna

### Przepływ

```
BC A (producent)
  API/CLI → Command → CommandBus → CommandHandler
    → UnitOfWork (SqlAlchemyUnitOfWorkBase) → Aggregate mutacja → stage_events()
    → commit: stan agregatu + event_outbox + audit (_write_staged_outbox)
    UoW / outbox writer → event_outbox|command_outbox
  EventOutboxRelay/CommandOutboxRelay → DeliveryTransport.deliver → broker
                                   (EnvelopeCodec.encode wykonywany wewnątrz transportu;
                                    JSON: event_id|command_id, contract_type,
                                    occurred_at, schema_version, payload, metadata)

BC B (konsument)
  broker → consumer/relay → EnvelopeCodec.decode → row w tabeli inbox (InboxStateMixin)
  InboxClaimService.claim_batch
    → SELECT ... FOR UPDATE SKIP LOCKED (PENDING/RETRY i przeterminowane PROCESSING)
    → status=PROCESSING, claimed_by, lease_until (krótka transakcja)
  InboxProcessorBase (Event/CommandInboxProcessor)
    _process_in_transaction
      → dispatch (bus) → handler w session scope
      → commit: efekt biznesowy + lokalny outbox + ack PROCESSED (jedna transakcja)
```

Powyższy diagram odpowiada przepływowi z [architecture-overview](architecture-overview.md), a jego poszczególne ogniwa są rozwinięte w [transactional-outbox](transactional-outbox.md), [relay](relay.md), [delivery-transport](delivery-transport.md), [inbox-lifecycle](inbox-lifecycle.md), [claim-lease](claim-lease.md), [inbox-processor](inbox-processor.md) i [heartbeat-lease](heartbeat-lease.md).

### Role komponentów

- **Outbox (producent)** — trwały bufor deliverable zapisywany atomowo ze stanem domeny przez `SqlAlchemyUnitOfWorkBase`; `published_at` pozostaje puste do czasu potwierdzonego transportu.
- **Relay** — `EventOutboxRelay`/`CommandOutboxRelay` (wspólny cykl w `OutboxRelayBase`) czyta odpowiednią tabelę outbox i publikuje kopertę do brokera. Pełny opis w [relay](relay.md).
- **Transport** — porty `IntegrationEventDeliveryTransport` i `CommandDeliveryTransport` (w `application/ports/transport/`), realizowane przez adaptery `RabbitEventDeliveryTransport`/`RabbitCommandDeliveryTransport`. `EnvelopeCodec` (w `messaging/event_transport/` i `messaging/command_transport/`) koduje kopertę (`EventDeliveryEnvelope`/`CommandDeliveryEnvelope`) do JSON z `contract_type`, `schema_version`, payloadem i metadanymi (bez `kind` i `outbox_id`). Szczegóły w [delivery-transport](delivery-transport.md).
- **Inbox (konsument)** — konsument generuje lokalne `event_inbox.id`/`command_inbox.id` i stosuje idempotencję po `(source_service, event_id|command_id)`.
- **Claim z lease** — `InboxClaimService.claim_batch()` przejmuje rekordy w krótkiej transakcji bez trzymania zamka na czas handlera (`SELECT ... FOR UPDATE SKIP LOCKED` na PostgreSQL; SQLite bez skip locked). Szczegóły w [claim-lease](claim-lease.md).
- **Processor** — `InboxProcessorBase` realizuje wspólny cykl claim→process→ack; podtypy `EventInboxProcessor` (dispatch przez `EventPublisher`), `CommandInboxProcessor` (dispatch przez port `CommandDispatcher` → `CommandBusPublisher`) dostarczają tylko deserializację, dispatch i wartość causation. Uruchamiany przez [polling-worker](polling-worker.md) (`PollingWorker.run()` → `task.run_once()`).
- **Handler w session scope** — `_process_in_transaction` publikuje sesję jako ambientowy scope (`DeliverySessionScope`), więc UoW handlera współdzieli tę samą sesję i odracza commit; jeden commit utrwala efekt + outbox + ack atomowo. Patrz [session-scope](session-scope.md).
- **Dedup** — idempotencja at-least-once wynika z unikalnego `(source_service, event_id|command_id)` na tabelach inbox (`on_conflict_do_nothing` przy insert) oraz warunkowego ack po `id + status + claimed_by`; wariant dzielący sesję procesora nie zapisuje efektu bez ack (jeden commit).
- **Ack warunkowy** — `_acknowledge_in_session` ustawia `PROCESSED` warunkowym UPDATE kluczowanym po lokalnym `inbox.id + status + claimed_by`; jeżeli lease wygasł i rekord przejął inny worker, ack nie zmienia wiersza (rowcount=0).

### At-least-once i brak utraty

- Producent: zapis w outboxie jest atomowy z efektem biznesowym → wiadomość nie ginie przed transportem.
- Konsument: potwierdzenie (ack `PROCESSED`) jest warunkowe i atomowe z efektem; awaria po efekcie, a przed ack, skutkuje redelivery — które jest no-op dzięki dedup na insert (`on_conflict_do_nothing` + unique `(source_service, event_id|command_id)`) oraz dzięki temu, że wariant dzielący sesję nie zapisuje efektu bez ack (jeden commit).
- Brak potwierdzenia → lease wygasa → rekord wraca do zbioru claimowalnego (reclaim).

## Kluczowe pliki

- `shell/platform/application/ports/transport/event_transport.py` (`IntegrationEventDeliveryTransport`, `EventDeliveryEnvelope`)
- `shell/platform/application/ports/transport/command_transport.py` (`CommandDeliveryTransport`, `CommandDeliveryEnvelope`)
- `shell/platform/domain/value_objects/inbox_status.py` (`InboxStatus`)
- `shell/platform/infrastructure/messaging/inbox/inbox_claim_service.py` (`InboxClaimService`)
- `shell/platform/infrastructure/messaging/delivery/inbox_processor_base.py` (`InboxProcessorBase`)
- `shell/platform/infrastructure/messaging/inbox/inbox_batch_result.py` (`InboxBatchResult`)
- `shell/platform/infrastructure/messaging/event/event_inbox_processor.py` (`EventInboxProcessor`)
- `shell/platform/infrastructure/messaging/command/command_inbox_processor.py` (`CommandInboxProcessor`)
- `shell/platform/infrastructure/serialization/integration_event/integration_event_serializer.py` (`IntegrationEventSerializer`)
- `shell/platform/infrastructure/messaging/command/sql_command_outbox_writer.py` (`SqlCommandOutboxWriter`, `SqlCommandDeliveryDispatcher`)
- `shell/platform/infrastructure/messaging/event_transport/envelope_codec.py` i `command_transport/envelope_codec.py` (`EnvelopeCodec`)
- `shell/platform/infrastructure/messaging/polling_worker.py` (`PollingWorker`, `PollingTask`, `PollingWorkerConfig`)
- `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py` (`SqlAlchemyUnitOfWorkBase`)
- `shell/platform/infrastructure/persistence/sql/models/mixins/inbox_state.py` (`InboxStateMixin`)

## Powiązane koncepcje

- [transactional-outbox](transactional-outbox.md)
- [inbox-lifecycle](inbox-lifecycle.md)
- [claim-lease](claim-lease.md)
- [inbox-processor](inbox-processor.md)
- [heartbeat-lease](heartbeat-lease.md)
- [polling-worker](polling-worker.md)
- [relay](relay.md)
- [delivery-transport](delivery-transport.md)
- [session-scope](session-scope.md)
- [tracing-context](tracing-context.md)
- [delivery-models](delivery-models.md)
- [integration-contracts](integration-contracts.md)
