---
name: idempotency-retry
description: Wzorce niezawodności w architekturze event-driven — idempotentność konsumentów, retry z exponential backoff, deduplikacja eventów, kolejki dead-letter, circuit breaker dla zewnętrznych zasobów. Używaj gdy implementujesz resilient integration, obsługę błędów w event handlerach, albo zabezpieczasz przed duplikatami.
---

# Idempotency / Retry / Circuit Breaker w Enterprise DDD

## 1. Inbox Pattern — Deduplikacja Eventów

W SHELL deduplikacja jest realizowana przez:
- **`OutboxToInboxRelay`**: `ON CONFLICT DO NOTHING` / `OR IGNORE` przy INSERT do inbox — ten sam event nie trafi dwa razy
- **`InboxProcessor`**: `SELECT WHERE processed_at IS NULL` — event przetworzony raz nie jest dispatchowany ponownie

## 2. Retry — fixed backoff (obecna implementacja)

`InboxProcessor` używa **fixed backoff**, nie exponential:

```python
max_retries: int = 3
retry_backoff_seconds: int = 30  # stałe opóźnienie, nie skalowane
```

- Po nieudanej próbie: `retry_count++`, `last_attempted_at = now`
- Kolejna próba możliwa dopiero po `retry_backoff_seconds` od `last_attempted_at`
- Po przekroczeniu `max_retries`: event oznaczany `processed_at = now` (tombstone — log + brak dalszych prób)
- Brak osobnej tabeli DLQ — event zostaje w inbox z `processed_at`

**TODO**: exponential backoff (2^attempt), jitter, dedykowana tabela DLQ.

## 3. Lokalizacja — obecne klasy

| Klasa | Lokalizacja | Opis |
|-------|-------------|------|
| `InboxProcessor` | `shell/platform/infrastructure/messaging/event/processor/inbox_processor.py` | Retry + backoff + tombstone DLQ |
| `OutboxToInboxRelay` | `shell/platform/infrastructure/messaging/event/outbox_to_inbox_relay.py` | Brak retry — propaguje błąd |
| `OutboxEventModel` | `shell/platform/infrastructure/persistence/sql/models/event/outbox_event.py` | Model outbox |
| `InboxEventModel` | `shell/platform/infrastructure/persistence/sql/models/event/inbox_event.py` | Model inbox z kolumnami retry |

**TODO**: brak dedykowanych katalogów `retry/`, `circuit_breaker/`, `dlq/` — to wszystko jest inline w inbox_processor.py.

## 4. Circuit Breaker — niezaimplementowany

**TODO**: SHELL nie ma implementacji Circuit Breaker. Brak klas, brak adapterów, brak konfiguracji. Wzorzec opisany w `retry-circuit-breaker-pattern` jest wyłącznie aspiracyjny.

## 5. Podsumowanie — Checklista

Implementując niezawodność:
- [x] Idempotentność przez inbox (`processed_at`, `ON CONFLICT DO NOTHING`)
- [ ] Exponential backoff (obecnie fixed 30s)
- [ ] Dedykowana tabela DLQ
- [ ] Circuit breaker dla zewnętrznych zasobów
- [ ] Retry dla OutboxToInboxRelay (obecnie brak)
- [ ] Monitoring i alerting na DLQ
