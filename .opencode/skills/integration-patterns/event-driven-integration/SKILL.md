---
name: event-driven-integration
description: Wzorce integracji zdarzeniowej — Transactional Outbox, Inbox, idempotencja, sagi, event ordering, DLQ, wersjonowanie eventów, CQRS na eventach. Używaj gdy implementujesz komunikację między agregatami/bounded context przez eventy, projektujesz schemat outbox, piszesz sagę choreograficzną, albo debugujesz problemy z kolejnością/zgubionymi eventami.
---

# Integracja zdarzeniowa w architekturze enterprise

Integracja zdarzeniowa pozwala agregatom i bounded context komunikować się bez bezpośrednich zależności. Zamiast wołać "zrób X na Y", emitujesz "X się wydarzyło" — zainteresowani subskrybują i reagują we własnym zakresie.

## Fundament: Transactional Outbox

Problem: jak zagwarantować że event jest opublikowany dokładnie wtedy gdy zmiana stanu jest zapisana w bazie? Nie możesz zrobić "save to DB + publish to broker" — jeśli jedno fejluje, drugie zostaje.

Rozwiązanie: zapisujesz event do tabeli `outbox_event` W TEJ SAMEJ TRANSAKCJI co zmiana domenowa. Wspólny `OutboxToTransportRelay` publikuje kopertę do brokera, a consumer docelowego BC zapisuje ją do własnego `inbox_event`. `EventInboxProcessor` dispatchuje ją do handlerów przez `EventBus`.

```
┌──────────────────────────────────────────────────────────────────┐
│ Transakcja 1 (UoW)                                               │
│   aggregate.domain_method() → append_event(DomainEvent)          │
│   ReflectiveIntegrationMapper → IntegrationEvent                 │
│   INSERT INTO outbox_event (event_type, payload, correlation_id) │
│   COMMIT — atomowo z zapisem agregatu                           │
└──────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────────┐
│ OutboxToTransportRelay.run_once()  (background task / scheduler)       │
│   SELECT FROM outbox_event WHERE published_at IS NULL            │
│     ORDER BY occurred_at LIMIT batch_size                        │
│     FOR UPDATE SKIP LOCKED  (pomija blokowane wiersze)          │
│   PUBLISH DeliveryEnvelope TO BROKER                              │
│   consumer INSERT INTO inbox_event (id, outbox_id, event_type,   │
│     payload, metadata)                                            │
│   UPDATE outbox_event SET published_at = now()                   │
│   COMMIT                                                         │
└──────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────────┐
│ EventInboxProcessor.run_once()  (background task / scheduler)          │
│   SELECT FROM inbox_event WHERE processed_at IS NULL             │
│     AND retry_count < max_retries                                │
│     AND (last_attempted_at IS NULL OR < backoff_cutoff)          │
│     FOR UPDATE SKIP LOCKED                                      │
│   for each row:                                                  │
│     deserialize → DomainEvent/IntegrationEvent                   │
│     set correlation_id + causation_id ContextVars                │
│     await EventBus.publish([event])                              │
│       → handler = factory(); await handler.handle(event)         │
│     on success: processed_at = now                               │
│     on failure: retry_count++, backoff, or DLQ (processed_at)    │
│   COMMIT                                                         │
└──────────────────────────────────────────────────────────────────┘
```

### Gwarancje

Outbox daje **at-least-once delivery**. Event może być dostarczony więcej niż raz (np. broker potwierdził, ale update `processed_at` nie doszedł). Dlatego każdy consumer musi być **idempotentny** — patrz Inbox Pattern.

### Schemat tabeli outbox (`OutboxEventModel`)

| Kolumna | Typ | Opis |
|---------|-----|------|
| `id` | str (PK) | Lokalny identyfikator outbox |
| `event_id` | str | Tożsamość faktu biznesowego |
| `source_service` | str | Bounded context nadawcy |
| `event_type` | str | Klasa eventu (np. `WorkflowCompletedEvent`) |
| `occurred_at` | datetime | Kiedy event wystąpił (UTC) |
| `payload` | JSONB | Serializowane pola eventu |
| `correlation_id` | str | Łączy eventy w jeden łańcuch przyczynowy (z ContextVar) |
| `causation_id` | str | ID eventu który spowodował ten event (z ContextVar) |
| `published_at` | datetime (nullable) | Kiedy transport potwierdził publikację |

## Inbox Pattern — idempotentny consumer

Problem: event może przyjść wielokrotnie (at-least-once). Consumer nie może przetworzyć go dwa razy.

Rozwiązanie: **EventInboxProcessor** (w SHELL) odczytuje `inbox_event`, deserializuje i dispatchuje do `EventBus` tylko dla nieprzetworzonych wierszy.

Idempotentność na dwóch poziomach:
1. **Relay**: `ON CONFLICT DO NOTHING` / `OR IGNORE` przy INSERT do inbox — ten sam event nie trafi dwa razy do inbox
2. **Processor**: `SELECT WHERE processed_at IS NULL` — event przetworzony raz nie jest ponownie dispatchowany

### Schemat tabeli inbox (`InboxEventModel`)

| Kolumna | Typ | Opis |
|---------|-----|------|
| `id` | str (PK) | Lokalny identyfikator inbox |
| `outbox_id` | str | Referencja do `outbox_event.id` nadawcy |
| `source_service` | str | Bounded context nadawcy |
| `event_type` | str | Klasa eventu (np. `WorkflowCompletedEvent`) |
| `occurred_at` | datetime | Kiedy event wystąpił |
| `payload` | JSONB | Serializowane pola eventu |
| `correlation_id` | str | Łańcuch przyczynowy (kopiowane z outbox) |
| `causation_id` | str | ID eventu który spowodował ten event |
| `received_at` | datetime | Kiedy consumer zapisał kopertę |
| `processed_at` | datetime (nullable) | Kiedy EventInboxProcessor dispatchował |
| `retry_count` | int (default 0) | Liczba prób (dodane w migracji 065) |
| `last_attempted_at` | datetime (nullable) | Ostatnia próba (do backoff) |
| `error` | str (nullable) | Komunikat błędu przy ostatniej próbie |

## Implementacja w SHELL — klasy

| Klasa | Lokalizacja | Odpowiedzialność |
|-------|-------------|------------------|
| `SqlAlchemyUnitOfWorkBase` | `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py` | W outbox w tej samej transakcji co agregat |
| `ReflectiveIntegrationMapper` | `shell/platform/infrastructure/mapping/reflective_integration_mapper.py` | Mapuje domain event → integration event |
| `OutboxToTransportRelay` | `shell/platform/infrastructure/messaging/transport/outbox_to_transport_relay.py` | Publikuje każdy outbox do brokera |
| `EventInboxProcessor` | `shell/platform/infrastructure/messaging/event/processor/event_inbox_processor.py` | Deserializuje, dispatchuje do EventBus, retry/DLQ |
| `EventBus` | `shell/platform/application/bus/event_bus.py` | In-memory dispatch do handlerów (lazy factories) |
| `DomainEventSerializer` | `shell/platform/infrastructure/serialization/event_serializer.py` | Serializacja/deserializacja eventów |
| `EventDeserializer` | `shell/platform/infrastructure/serialization/event_deserializer.py` | Deserializacja z rejestrem klas |
| `build_event_registry()` | `shell/platform/infrastructure/serialization/event_registry.py` | Auto-generowany rejestr event → klasa |

## Saga — choreografia vs orkiestracja

> **Zakres**: Architektura SHELL przewiduje sagę w warstwie `shell/process/`. Poniższy opis definiuje wzorzec docelowy.

Saga to wzorzec realizacji długotrwałego procesu biznesowego przez sekwencję lokalnych transakcji. Każdy krok to osobna transakcja na pojedynczym agregacie.

### Choreografia (event-driven saga)

Każdy krok słucha eventów poprzedniego i emituje event dla następnego. Choreografia rozdziela koordynacje pomiedzy uczestnikow.

**Kiedy użyć:**
- Prosty flow liniowy (≤ 5 kroków)
- Wszystkie kroki w jednym bounded context
- Prosty flow korzysta z lokalnych transakcji i lokalnej obsługi błędów.

### Orkiestracja (orchestration-based saga)

Centralny koordynator (Saga Manager / Process Manager) śledzi stan całego procesu i wywołuje kolejne kroki.

**Kiedy użyć:**
- Złożony flow z warunkami, pętlami, timeoutami
- Wiele bounded context
- Potrzeba centralnego widoku stanu procesu
- Kompensacja gdy flow się nie powiedzie

## Event ordering i śledzenie przyczyn

### FIFO per aggregate

Eventy z tego samego agregatu są przetwarzane w kolejności. Eventy z różnych agregatów mogą być przetwarzane równolegle.

Broker gwarantuje kolejność tylko w ramach jednego partition key (np. `aggregate_id`). Consumer używa `aggregate_id` jako partition key.

## Event sourcing — różnica od outbox

Event sourcing przechowuje stan agregatu jako sekwencję eventów zamiast snapshotu. Każda zmiana to nowy event. Stan agregatu jest odtwarzany przez replay eventów.

**Outbox** — event jest skutkiem ubocznym zapisu stanu. Stan jest źródłem prawdy.
**Event sourcing** — event JEST źródłem prawdy. Stan jest pochodną (projekcją).

Event sourcing stosuj gdy potrzebujesz:
- Pełnego audytu każdej zmiany (kto, co, kiedy)
- Odtwarzania stanu na dowolny moment w przeszłości (time travel)
- Alternatywnych projekcji — te same eventy, różne read modele

Dla większości przypadków outbox jest wystarczający. Event sourcing dodaje złożoność (snapshoty, replay, versioning eventów).

## Konwencje

- `OutboxToTransportRelay`, broker consumer i `EventInboxProcessor` działają w osobnych transakcjach od zapisu domenowego
- Concurrency: `FOR UPDATE SKIP LOCKED` na PostgreSQL, pomijane na SQLite
- Retry: fixed backoff (30s), max 3 próby, po wyczerpaniu `processed_at = now` (tombstone DLQ)
- Tracing: `correlation_id` i `causation_id` propagowane przez `ContextVar` → outbox → inbox → handler
