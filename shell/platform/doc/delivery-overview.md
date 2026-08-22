# Przepływ delivery end-to-end

## Cel / Co realizuje

Opisuje jedną ścieżkę przekazywania deliverable (event, message, command) między bounded contextami platformy SHELL: zapis w transakcyjnym outboxie, wspólny relay do transportu i brokera, zapis w inboxie, claim z lease, procesor oraz atomowy ack w konsumenckim BC. Wszystkie rodzaje korzystają z `OutboxToTransportRelay`, `DeliveryEnvelope`, `EnvelopeCodec` i odpowiedniego procesora inbox.

## Problem

Bounded contexts są od siebie niezależne (oddzielne bazy, procesy, cykle życia transakcji), a mimo to muszą wymieniać stan bez tracenia wiadomości. Bezpośrednie publikowanie do brokera w trakcie transakcji daje utratę wiadomości przy awarii między commitem a wysłaniem (dual write). Z drugiej strony konsument odbierający wiadomość at-least-once może ją przetworzyć dwukrotnie przy redelivery. Potrzebny jest mechanizm: trwałego zapisu deliverable atomowo ze stanem domeny (outbox), transportu, który nie gubi wiadomości, oraz konsumpcji z deduplikacją, identyfikowalnością (correlation/causation) i atomowym potwierdzeniem.

## Realizacja techniczna

### Przepływ

```
BC A (producent)
  API/CLI → Command → CommandBus → CommandHandler
    → UnitOfWork (SqlAlchemyUnitOfWorkBase) → Aggregate mutacja → stage_events()
    → commit: stan agregatu + outbox_event + audit (_write_staged_outbox)
    UoW / outbox writer → outbox_event|outbox_message|outbox_command
  OutboxToTransportRelay → EnvelopeCodec.encode → DeliveryTransport.deliver → broker
                                   (JSON: kind, outbox_id, contract_type,
                                    occurred_at, schema_version, payload, metadata)

BC B (konsument)
  broker → consumer/relay → EnvelopeCodec.decode → row w tabeli inbox (InboxStateMixin)
  InboxClaimService.claim_batch
    → SELECT ... FOR UPDATE SKIP LOCKED (PENDING/RETRY i przeterminowane PROCESSING)
    → status=PROCESSING, claimed_by, lease_until (krótka transakcja)
  InboxProcessorBase (Event/Message/CommandInboxProcessor)
    _process_in_transaction
      → is_duplicate? (ProcessedDeliveryStore) → dispatch (bus) → handler w session scope
      → commit: efekt biznesowy + lokalny outbox + ack PROCESSED (jedna transakcja)
```

Powyższy diagram odpowiada przepływowi z [architecture-overview](architecture-overview.md), a jego poszczególne ogniwa są rozwinięte w [transactional-outbox](transactional-outbox.md), [relay](relay.md), [delivery-transport](delivery-transport.md), [inbox-lifecycle](inbox-lifecycle.md), [claim-lease](claim-lease.md), [inbox-processor](inbox-processor.md), [heartbeat-lease](heartbeat-lease.md) i [processed-delivery-dedup](processed-delivery-dedup.md).

### Role komponentów

- **Outbox (producent)** — trwały bufor deliverable zapisywany atomowo ze stanem domeny przez `SqlAlchemyUnitOfWorkBase`; `published_at` pozostaje puste do czasu potwierdzonego transportu.
- **Relay** — jedyny `OutboxToTransportRelay` czyta odpowiednią tabelę outbox i publikuje kopertę do brokera. Pełny opis w [relay](relay.md).
- **Transport** — port `DeliveryTransport`, realizowany przez adaptery brokerskie. `EnvelopeCodec` koduje `DeliveryEnvelope` do JSON z `outbox_id`, `contract_type`, `schema_version`, payloadem i metadanymi. Szczegóły w [delivery-transport](delivery-transport.md).
- **Inbox (konsument)** — konsument generuje lokalne `inbox_event.id`/`inbox_message.id`/`inbox_command.id`, zapisuje `outbox_id` jako referencję do rekordu nadawcy i stosuje idempotencję po źródle oraz outboxie.
- **Claim z lease** — `InboxClaimService.claim_batch()` przejmuje rekordy w krótkiej transakcji bez trzymania zamka na czas handlera (`SELECT ... FOR UPDATE SKIP LOCKED` na PostgreSQL; SQLite bez skip locked). Szczegóły w [claim-lease](claim-lease.md).
- **Processor** — `InboxProcessorBase` realizuje wspólny cykl claim→process→ack; podtypy `EventInboxProcessor` (dispatch przez `EventPublisher`), `MessageInboxProcessor` (dispatch przez `MessagePublisher`), `CommandInboxProcessor` (dispatch przez `CommandBus`) dostarczają tylko deserializację, dispatch i wartość causation. Uruchamiany przez [polling-worker](polling-worker.md) (`PollingWorker.run()` → `task.run_once()`).
- **Handler w session scope** — `_process_in_transaction` publikuje sesję jako ambientowy scope (`DeliverySessionScope`), więc UoW handlera współdzieli tę samą sesję i odracza commit; jeden commit utrwala efekt + outbox + ack atomowo. Patrz [session-scope](session-scope.md).
- **Dedup (fallback)** — dla handlerów, które nie mogą współdzielić transakcji procesora, wiersz `processed_delivery` zapisywany atomowo z efektem; `is_duplicate` sprawdzany przed dispatch. Patrz [processed-delivery-dedup](processed-delivery-dedup.md).
- **Ack warunkowy** — `_acknowledge_in_session` ustawia `PROCESSED` warunkowym UPDATE kluczowanym po lokalnym `inbox.id + status + claimed_by`; jeżeli lease wygasł i rekord przejął inny worker, ack nie zmienia wiersza (rowcount=0).

### At-least-once i brak utraty

- Producent: zapis w outboxie jest atomowy z efektem biznesowym → wiadomość nie ginie przed transportem.
- Konsument: potwierdzenie (ack `PROCESSED`) jest warunkowe i atomowe z efektem; awaria po efekcie, a przed ack, skutkuje redelivery — które jest no-op dzięki dedup (`processed_delivery`) lub dzięki temu, że wariant dzielący sesję nie zapisuje efektu bez ack (jeden commit).
- Brak potwierdzenia → lease wygasa → rekord wraca do zbioru claimowalnego (reclaim).

## Kluczowe pliki

- `shell/platform/application/ports/delivery_transport.py` (`DeliveryTransport`, `DeliveryEnvelope`)
- `shell/platform/application/ports/delivery_dedup_store.py` (`DeliveryDedupStore`)
- `shell/platform/domain/value_objects/inbox_status.py` (`InboxStatus`)
- `shell/platform/infrastructure/messaging/inbox/inbox_claim_service.py` (`InboxClaimService`)
- `shell/platform/infrastructure/messaging/inbox/inbox_processor_base.py` (`InboxProcessorBase`)
- `shell/platform/infrastructure/messaging/inbox/inbox_batch_result.py` (`InboxBatchResult`)
- `shell/platform/infrastructure/messaging/inbox/processed_delivery_store.py` (`ProcessedDeliveryStore`)
- `shell/platform/infrastructure/messaging/event/processor/event_inbox_processor.py` (`EventInboxProcessor`)
- `shell/platform/infrastructure/messaging/message/processor/message_inbox_processor.py` (`MessageInboxProcessor`)
- `shell/platform/infrastructure/messaging/command/processor/command_inbox_processor.py` (`CommandInboxProcessor`)
- `shell/platform/infrastructure/serialization/event/integration_event_serializer.py` (`IntegrationEventSerializer`)
- `shell/platform/infrastructure/messaging/message/sql_message_outbox_publisher.py` (`SqlMessageOutboxPublisher`)
- `shell/platform/infrastructure/messaging/command/sql_command_outbox_publisher.py` (`SqlCommandOutboxPublisher`)
- `shell/platform/infrastructure/messaging/transport/envelope_codec.py` (`EnvelopeCodec`)
- `shell/platform/infrastructure/messaging/polling_worker.py` (`PollingWorker`, `PollingTask`, `PollingWorkerConfig`)
- `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py` (`SqlAlchemyUnitOfWorkBase`)
- `shell/platform/infrastructure/persistence/sql/models/mixins/inbox_state.py` (`InboxStateMixin`)
- `shell/platform/infrastructure/persistence/sql/models/processed_delivery.py` (`build_processed_delivery_model`)

## Powiązane koncepcje

- [transactional-outbox](transactional-outbox.md)
- [inbox-lifecycle](inbox-lifecycle.md)
- [claim-lease](claim-lease.md)
- [inbox-processor](inbox-processor.md)
- [heartbeat-lease](heartbeat-lease.md)
- [processed-delivery-dedup](processed-delivery-dedup.md)
- [polling-worker](polling-worker.md)
- [relay](relay.md)
- [delivery-transport](delivery-transport.md)
- [session-scope](session-scope.md)
- [tracing-context](tracing-context.md)
- [delivery-models](delivery-models.md)
- [integration-contracts](integration-contracts.md)
