---
name: idempotency-retry
description: Wzorce niezawodności w architekturze event-driven — idempotentność konsumentów, retry z exponential backoff, deduplikacja eventów, kolejki dead-letter, circuit breaker dla zewnętrznych zasobów. Używaj gdy implementujesz resilient integration, obsługę błędów w event handlerach, albo zabezpieczasz przed duplikatami.
---

# Idempotency / Retry / Circuit Breaker w Enterprise DDD

## 1. Inbox Pattern — Deduplikacja Eventów

W SHELL deduplikacja jest realizowana przez:
- **`RabbitEventInboxConsumer`** / **`RabbitCommandInboxConsumer`**: idempotentny insert koperty do inbox po `source_service + outbox_id` — ta sama publikacja nie tworzy drugiego rekordu logicznego
- **`EventInboxProcessor`**: `SELECT WHERE processed_at IS NULL` — event przetworzony raz nie jest dispatchowany ponownie

## 2. Retry — fixed backoff (obecna implementacja)

`EventInboxProcessor` używa **fixed backoff**, nie exponential:

```python
max_retries: int = 3
retry_backoff_seconds: int = 30  # stałe opóźnienie, nie skalowane
```

- Po nieudanej próbie: `retry_count++`, `last_attempted_at = now`
- Kolejna próba możliwa dopiero po `retry_backoff_seconds` od `last_attempted_at`
- Po przekroczeniu `max_retries`: event oznaczany `processed_at = now` (tombstone — log + brak dalszych prób)
- Tombstone DLQ korzysta z wiersza inbox z `processed_at`.

**TODO**: exponential backoff (2^attempt), jitter, dedykowana tabela DLQ.

## 3. Lokalizacja — obecne klasy

| Klasa | Lokalizacja | Opis |
|-------|-------------|------|
| `EventInboxProcessor` | `shell/platform/infrastructure/messaging/event/processor/event_inbox_processor.py` | Retry + backoff + tombstone DLQ |
| `OutboxToTransportRelay` | `shell/platform/infrastructure/messaging/event_transport/outbox_to_transport_relay.py` | Publikuje outbox przez broker |
| `OutboxEventModel` | `shell/platform/infrastructure/persistence/sql/models/event_delivery.py` | Model outbox |
| `InboxEventModel` | `shell/platform/infrastructure/persistence/sql/models/event_delivery.py` | Model inbox z kolumnami retry |
| `RabbitEventInboxConsumer` | `shell/platform/infrastructure/messaging/event_transport/rabbit/` | Konsument kopert eventów z brokera |
| `RabbitCommandInboxConsumer` | `shell/platform/infrastructure/messaging/command_transport/rabbit/` | Konsument kopert komend z brokera |

**Zakres implementacji**: retry, backoff i tombstone sa skupione w `event_inbox_processor.py`. Dedykowane katalogi sa kierunkiem dalszego rozwoju.

## 4. Circuit Breaker — kierunek rozwoju

Wzorzec `retry-circuit-breaker-pattern` opisuje docelowy model Circuit Breaker dla zewnetrznych zasobow. Implementacja wymaga dedykowanych klas, adapterow i konfiguracji.

## 5. Podsumowanie — Checklista

Implementując niezawodność:
- [x] Idempotentność przez inbox (`processed_at`, `ON CONFLICT DO NOTHING`)
- [ ] Exponential backoff (obecnie fixed 30s)
- [ ] Dedykowana tabela DLQ
- [ ] Circuit breaker dla zewnętrznych zasobów
- [ ] Monitoring i alerting na błędy transportu outbox
- [ ] Monitoring i alerting na DLQ
