---
name: event-driven-integration
description: Wzorce integracji zdarzeniowej — Transactional Outbox, Inbox, idempotencja, sagi, event ordering, DLQ, wersjonowanie eventów, CQRS na eventach. Używaj gdy implementujesz komunikację między agregatami/bounded context przez eventy, projektujesz schemat outbox, piszesz sagę choreograficzną, albo debugujesz problemy z kolejnością/zgubionymi eventami.
---

# Integracja zdarzeniowa w architekturze enterprise

Integracja zdarzeniowa pozwala agregatom i bounded context komunikować się bez bezpośrednich zależności. Zamiast wołać "zrób X na Y", emitujesz "X się wydarzyło" — zainteresowani subskrybują i reagują we własnym zakresie.

## Fundament: Transactional Outbox

Problem: jak zagwarantować że event jest opublikowany dokładnie wtedy gdy zmiana stanu jest zapisana w bazie? Nie możesz zrobić "save to DB + publish to broker" — jeśli jedno fejluje, drugie zostaje.

Rozwiązanie: zapisujesz event do tabeli `outbox_event` W TEJ SAMEJ TRANSAKCJI co zmiana domenowa. Osobny proces (OutboxRelay) odczytuje nieopublikowane eventy z outbox i publikuje je do brokera.

```
┌─────────────────────────────────────────────────────┐
│ Transaction 1                                        │
│   INSERT INTO aggregate (...)                        │
│   INSERT INTO outbox_event (event_id, type, payload) │
│   COMMIT — oba zapisy atomowe                       │
└─────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│ OutboxRelay (osobny proces / background task)        │
│   SELECT * FROM outbox_event WHERE processed_at IS NULL ORDER BY created_at
│   FOR EACH event:                                    │
│     → publish do brokera (RabbitMQ / Kafka / ...)    │
│     → UPDATE outbox_event SET processed_at = now()   │
└─────────────────────────────────────────────────────┘
```

### Gwarancje

Outbox daje **at-least-once delivery**. Event może być dostarczony więcej niż raz (np. broker potwierdził, ale update `processed_at` nie doszedł). Dlatego każdy consumer musi być **idempotentny** — patrz Inbox Pattern.

### Schemat tabeli outbox

| Kolumna | Typ | Opis |
|---------|-----|------|
| `id` | UUID / int | Primary key |
| `event_id` | UUID | Unikalny identyfikator eventu |
| `aggregate_id` | string | ID agregatu który wyemitował event |
| `aggregate_type` | string | Typ agregatu (np. `Workflow`) |
| `event_type` | string | Klasa eventu (np. `WorkflowCompletedEvent`) |
| `payload` | JSONB / TEXT | Pełny event jako JSON |
| `correlation_id` | string (nullable) | Łączy eventy w jeden łańcuch przyczynowy |
| `causation_id` | string (nullable) | ID eventu który bezpośrednio spowodował ten event |
| `created_at` | timestamp | Kiedy event został zapisany do outbox |
| `processed_at` | timestamp (nullable) | Kiedy OutboxRelay opublikował event |
| `retry_count` | int (default 0) | Liczba prób publikacji |
| `error` | text (nullable) | Ostatni błąd przy publikacji |

## Inbox Pattern — idempotentny consumer

Problem: event może przyjść wielokrotnie (at-least-once). Consumer nie może przetworzyć go dwa razy.

Rozwiązanie: przed przetworzeniem eventu sprawdź czy jego `event_id` już jest w tabeli inbox. Jeśli tak — pomiń (event już był przetworzony). Jeśli nie — przetwórz + zapisz `event_id` do inbox.

```
Consumer.handle(event):
    if inbox.contains(event.event_id):  → SKIP
    try:
        process(event)                   → business logic
        inbox.add(event.event_id)        → mark as processed
    except Exception:
        retry / DLQ                      → error handling
```

### Schemat tabeli inbox

| Kolumna | Typ | Opis |
|---------|-----|------|
| `event_id` | UUID | Primary key — identyfikator przetworzonego eventu |
| `processed_at` | timestamp | Kiedy event został przetworzony |

## Saga — choreografia vs orkiestracja

Saga to wzorzec realizacji długotrwałego procesu biznesowego przez sekwencję lokalnych transakcji. Każdy krok to osobna transakkcja na pojedynczym agregacie.

### Choreografia (event-driven saga)

Każdy krok słucha eventów poprzedniego i emituje event dla następnego. Nie ma centralnego koordynatora.

```
OrderConfirmedEvent → InventoryHandler.reserve()
                       → StockReservedEvent → PaymentHandler.charge()
                                                → PaymentCompletedEvent → ShipmentHandler.ship()
```

**Kiedy użyć:**
- Prosty flow liniowy (≤ 5 kroków)
- Wszystkie kroki w jednym bounded context
- Nie ma potrzeby timeoutów / kompensacji na poziomie całej sagi

### Orkiestracja (orchestration-based saga)

Centralny koordynator (Saga Manager / Process Manager) śledzi stan całego procesu i wywołuje kolejne kroki.

```
SagaOrchestrator:
    1. Wyślij ReserveInventory command
    2. Odbierz InventoryReserved event
    3. Wyślij ChargePayment command
    4. Odbierz PaymentCompleted event
    5. Wyślij CreateShipment command
```

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

## Kiedy czytasz references

- Implementujesz outbox / inbox pierwzy raz → `references/outbox-inbox.md`
- Projektujesz długotrwały proces biznesowy między agregatami → `references/saga-patterns.md`
- Projektujesz schemat nowego eventu domenowego / integracyjnego → `references/event-design.md`

## Konwencje

- OutboxRelay publikuje eventy w osobnej transakcji od zapisu domenowego
