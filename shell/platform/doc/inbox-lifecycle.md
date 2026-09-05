# Cykl życia rekordu inbox (maszyna stanów)

## Cel / Co realizuje

Definiuje jawny, współdzielony cykl życia rekordu inbox: enum `InboxStatus` (w `shell/platform/domain/value_objects/inbox_status.py`) oraz kolumny operacyjne i indeksy w `InboxStateMixin` (w `shell/platform/infrastructure/persistence/sql/models/mixins/inbox_state.py`). Event i command inboxy dzielą ten sam cykl operacyjny, więc kolumny żyją w jednym mixinie platformowym zamiast być duplikowane w każdym modelu.

## Problem

Rekord inbox przechodzi przez stany: oczekiwanie, przetwarzanie (z lease), retry z backoffem, dead letter. Bez jawnego stanu każda kolejna operacja (claim, ack, retry) musiałaby wnioskować o przeszłości z rozproszonych kolumn, a równoległe workery nie miałyby deterministycznej podstawy do odzyskiwania rekordów po awarii workera. Potrzebny jest jeden stanorowisty atrybut `status`, kolumny czasu/atrybucji (kto, do kiedy, ile prób, jaki błąd) oraz indeksy pokrywające dokładnie zapytania claima i sprawdzania wygasłego lease.

## Realizacja techniczna

### InboxStatus

`InboxStatus(ValueObject, StrEnum)` definiuje pięć wartości:

```
PENDING        nowy rekord, oczekuje na claim (next_attempt_at <= now)
PROCESSING     zaclaimowany przez workera; lease_until = granica posiadania
PROCESSED      przetworzony i potwierdzony (ack)
RETRY          nieudany, zaplanowany na ponowną próbę (next_attempt_at = backoff)
DEAD_LETTER    przekroczone max_retries (lub nieobsługiwany schema_version)
```

Dziedziczenie po `ValueObject` + `StrEnum` daje wartości porównywalne jako stringi i traktowalne jako obiekty domeny. Domyślną wartością kolumny `status` jest `InboxStatus.PENDING.value`, więc każdy wiersz zaczyna w tym samym, jawnym stanie.

### InboxStateMixin — kolumny operacyjne

Kolumny deklarowane jako `Mapped[...]` z `@declared_attr` `__table_args__` (indeksy budowane na bazie `cls.__tablename__`):

| Kolumna | Typ / domyślna | Znaczenie |
|---|---|---|
| `status` | `str`, nie-null, default `PENDING` | stan cyklu życia |
| `next_attempt_at` | `DateTime(timezone=True)`, nie-null, default `_default_next_attempt_at()` (now UTC, `microsecond=0`) | najwcześniejszy moment claima; domyślnie czas insertu (odpowiednik `received_at`), więc zapytanie claima nie musi special-case'ować NULL |
| `lease_until` | `DateTime(timezone=True)`, nullable, default `None` | granica lease; rekord `PROCESSING` z `lease_until < now` jest claimowalny ponownie |
| `claimed_by` | `str`, nullable, default `None` | identyfikator workera (owner) |
| `processed_at` | `DateTime(timezone=True)`, nullable | czas udanego ack |
| `failed_at` | `DateTime(timezone=True)`, nullable | czas trafienia do DLQ |
| `last_attempted_at` | `DateTime(timezone=True)`, nullable | czas ostatniej próby |
| `retry_count` | `int`, nie-null, default `0` | liczba dotychczasowych prób |
| `error` | `str`, nullable | pełny tekst błędu (zarezerwowany; obecnie nie jest zapisywany — szczegóły błędów trafiają do `error_code`/`error_message`) |
| `error_code` | `str`, nullable | kod błędu (`HANDLER_ERROR`, `DESERIALIZATION_ERROR`, `UNSUPPORTED_SCHEMA_VERSION` ...) |
| `error_message` | `str`, nullable | komunikat błędu |
| `schema_version` | `int`, nie-null, default `1` | wersja schematu payloadu (walidacja/upcast) |

Kolumny `received_at`, `correlation_id`, `causation_id`, `payload` nie są w mixinie — dostarcza je konkretny model delivery (kontrakt dla claima opisuje protokół `InboxStateModel` w `inbox_claim_service.py`, który wymaga m.in. `received_at`; protokół `_ClaimedInboxRow` w `inbox_processor_base.py` wymaga `correlation_id` i `causation_id`).

### Indeksy

`build_inbox_state_indexes(table_name)` zwraca dwa indeksy:

- `ix_{table}_status_next_attempt_received` — `(status, next_attempt_at, received_at)`: pokrywa selekcję rekordów `PENDING`/`RETRY` z `next_attempt_at <= now` (kolejność po `received_at`);
- `ix_{table}_status_lease_until` — `(status, lease_until)`: pokrywa selekcję wygasłych rekordów `PROCESSING` z `lease_until < now` (reclaim).

### Przejścia stanów (kto je wykonuje)

- `PENDING → PROCESSING` — `InboxClaimService.claim_batch()` (status, `claimed_by`, `lease_until`; commit w krótkiej transakcji). Szczegóły: [claim-lease](claim-lease.md).
- `RETRY → PROCESSING` — ten sam claim: rekordy `RETRY` wchodzą w zakres zapytania, gdy `next_attempt_at <= now`.
- `PROCESSING → PROCESSING` (przejęcie) — rekord `PROCESSING` z wygasłym `lease_until < now` jest claimowalny ponownie (reclaim po awarii workera).
- `PROCESSING → PROCESSED` — `InboxProcessorBase._acknowledge_in_session()`: warunkowy UPDATE (`id`, `status = PROCESSING`, `claimed_by = worker_id`) ustawiający `PROCESSED`, `processed_at`, czyści `lease_until`, `claimed_by`, `retry_count`, `last_attempted_at`, `error_code`, `error_message`.
- `PROCESSING → RETRY` — `InboxProcessorBase._schedule_failure()` gdy nie przekroczono `max_retries`: ustawia `RETRY`, `next_attempt_at = now + backoff`, `retry_count = next_retry_count`, `error_code`, `error_message`.
- `PROCESSING → DEAD_LETTER` — `_schedule_failure()` gdy `next_retry_count >= max_retries` lub błąd walidacji `UNSUPPORTED_SCHEMA_VERSION` (`immediate_dead_letter=True`): ustawia `DEAD_LETTER`, `failed_at`, loguje `critical`.

Przejścia między stanami realizowane są wyłącznie przez procesor i serwis claima; nie istnieją statusy zarezerwowane dla przepływów migracyjnych.

### Deduplikacja (idempotencja at-least-once)

Idempotencja nie wymaga osobnej tabeli `processed_delivery` — jest zapewniona na dwóch poziomach:

1. **Insert** — konsumenci zapisują wiersz inbox przez `pg_insert(...).on_conflict_do_nothing()`; unikalny `(source_service, event_id|command_id)` (constraint `uq_event_inbox_source_event` / `uq_command_inbox_source_command`) sprawia, że redelivery tej samej wiadomości jest no-op na etapie zapisu.
2. **Ack** — `_acknowledge_in_session` wykonuje warunkowy UPDATE kluczowany po `id + status = PROCESSING + claimed_by`; jeżeli lease wygasł i rekord przejął inny worker, ack nie zmienia wiersza (rowcount=0).

## Kluczowe pliki

- `shell/platform/domain/value_objects/inbox_status.py`
- `shell/platform/infrastructure/persistence/sql/models/mixins/inbox_state.py`
- `shell/platform/infrastructure/messaging/inbox/inbox_claim_service.py` (protokół `InboxStateModel`, przejścia PENDING/RETRY → PROCESSING)
- `shell/platform/infrastructure/messaging/delivery/inbox_processor_base.py` (przejścia → PROCESSED / RETRY / DEAD_LETTER)

## Powiązane koncepcje

- [delivery-overview](delivery-overview.md)
- [claim-lease](claim-lease.md)
- [inbox-processor](inbox-processor.md)
- [heartbeat-lease](heartbeat-lease.md)
- [envelope-versioning](envelope-versioning.md)
- [delivery-models](delivery-models.md)
- [sqlalchemy-persistence](sqlalchemy-persistence.md)
