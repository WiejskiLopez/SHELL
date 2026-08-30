---
name: review-event-driven-integration
description: Weryfikacja integracji zdarzeniowej — outbox/inbox, idempotencja, eventy domenowe vs integracyjne, wersjonowanie eventów, kolejność, DLQ, sagi, tracing context. Używaj przy code review komunikacji między agregatami/BC przez eventy.
---

# Review — Integracja zdarzeniowa

> Zdarzenia to jedyna prosta droga między BC — ale tylko gdy spełniają kontrakty niezawodności.

## 1. Outbox / Inbox

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Zapis eventu do outbox atomowo z zapisem stanu agregatu | publish przed commit; event w osobnej transakcji | **CRITICAL** |
| Konsument idempotentny przez inbox (`event_id` deduplikacja) | przetwarzanie bez ochrony przed duplikatem | **CRITICAL** |
| Event opublikowany i potwierdzony dopiero po trwałym zapisie | ack przed zapisem outbox | **CRITICAL** |
| Brak zgubionych eventów przy restarcie (odzysk z outbox) | outbox czyszczony bez potwierdzenia | HIGH |

Patrz `event-driven-integration`, `idempotent-handler-pattern`.

## 2. Eventy domenowe vs integracyjne

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Eventy domenowe trzymane wewnątrz BC, nie publikowane na zewnątrz surowo | internal domain event wysyłany na integracyjny bus | HIGH |
| Do integracji używane DTO/integration events (kontrakt zewnętrzny), nie wewnętrzne modele | aggregation/BC narażone na szczątkowe eventy | HIGH |
| Nazwy eventów w czasie przeszłym, związane z faktem zaistniałym | event jako prośba/komenda (`CreateUser`) | MEDIUM |
| Semantyka zdarzeń spójna z faktami (affirmative facts) | event opisujący brak zaistnienia | HIGH |

Patrz `integration-event`, `domain-event`, `event-semantics`, `affirmative-facts` (architectural-discipline).

## 3. Spójność i kolejność zdarzeń

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Eventy wersjonowane (schema version, namespace) przy zmianach | zmiana eventu bez wersji | HIGH |
| Kolejność kluczowa zachowana (partition key by aggregate/entity) | eventy podmiotu rozproszone bez determinizmu | HIGH |
| Retry z exponential backoff + DLQ dla nieprzetwarzalnych | rzucony event ginie bez DLQ | HIGH |
| Sagi mają kompensacje/sczytowny stan procesu | saga bez kompensacji/i bez trwałości stanu | **CRITICAL** |

Patrz `saga`, `saga-structure`, `idempotency-retry`.

## 4. Tracing context

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| `correlation_id`/`causation_id`/`event_id` propagowane przez outbox/inbox | nowy event bez korelacji z przyczyną | HIGH |
| Envelope niesie tracing metadata | identyfikatory lost poza outbox | MEDIUM |
| Logi eventów zawierają correlation_id | log bez korelacji → brak debugowalności | MEDIUM |

Patrz `tracing-context`.

## 5. Handler / listener

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Handler subskrybuje event i jest bezstanowy | handler z pamięcią między eventami | HIGH |
| Handler nie robi side-effectów poza kontraktem | handler pisze do 3 agregatów bez koordynacji | MEDIUM |
| Powtórny event (duplicate) nie produkuje drugiego efektu | podwójny zapis/drugi email | **CRITICAL** |

## 6. Checklista finalna

- [ ] Outbox atomowo z zapisem; inbox z deduplikacją.
- [ ] Integration events wersjonowane, korelowane (correlation/causation).
- [ ] DLQ + retry dla błędów przetwarzania.
- [ ] Sagi kompensowane i trwałe.
- [ ] Zero nieidempotentnych konsumentów.