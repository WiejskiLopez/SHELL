---
name: idempotency-retry
description: Wzorce niezawodności w architekturze event-driven — idempotentność konsumentów, retry z exponential backoff, deduplikacja eventów, kolejki dead-letter, circuit breaker dla zewnętrznych zasobów. Używaj gdy implementujesz resilient integration, obsługę błędów w event handlerach, albo zabezpieczasz przed duplikatami.
---

# Idempotency / Retry / Circuit Breaker w Enterprise DDD

## 1. Inbox Pattern — Deduplikacja Eventów

Inbox przechowuje ID przetworzonych eventów — zapobiega wielokrotnemu przetworzeniu.

## 2. Retry z Exponential Backoff

Dla błędów przejściowych (transient faults) — retry z rosnącym opóźnieniem.

## 3. Lokalizacja

```
# Polityki retry i circuit breaker
shell/infrastructure/platform/retry/
shell/infrastructure/platform/circuit_breaker/
shell/infrastructure/platform/inbox/
shell/infrastructure/platform/dlq/
```

## 4. Podsumowanie — Checklista

Implementując niezawodność:
- [ ] Monitoring retry i DLQ
- [ ] Testy dla każdego scenariusza awarii
