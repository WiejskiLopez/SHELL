# Relay outbox (OutboxToTransportRelay i outbox-to-inbox relays)

## Cel / Co realizuje

`OutboxToTransportRelay` (w `shell/platform/infrastructure/messaging/transport/outbox_to_transport_relay.py`) jest mostem producenta między transactional outbox a brokerem: czyta niepublikowane wiersze `outbox_*` i publikuje je przez `DeliveryTransport`. Trzy warianty outbox-to-inbox — `EventOutboxToInboxRelay`, `MessageOutboxToInboxRelay`, `CommandOutboxToInboxRelay` — czytają oczekujące wiersze outbox danego rodzaju i batchowo wstawiają je do tabeli inbox (np. jako jednorazowa/okresowa migracja między dwiema bazami BC). Wszystkie relaye oznaczają `published_at` dopiero po sukcesie i używają `FOR UPDATE SKIP LOCKED` na PostgreSQL.

## Problem

Transactional outbox gwarantuje atomowość zapisu domeny i rekordu outbox, ale nie przenosi danych na broker ani do docelowego BC. Potrzebny jest proces, który bezpiecznie opublikuje oczekujące wiersze (producent), oraz mechanizm wpuszczenia już spublikowanych rekordów do inbox innego BC bez podwójnego przetwarzania. Kluczowe problemy: nie wolno oznaczyć wiersza jako opublikowanego przed faktycznym sukcesem (utrata danych przy crashu), równoległe procesy nie mogą podwójnie pobierać tych samych wierszy (konkurencja), a inserując do docelowego inbox trzeba być idempotentnym (dedup po `delivery_id`).

## Realizacja techniczna

### OutboxToTransportRelay (producent outbox → broker)

Protokoły `DeliveryOutboxModel` (kolumny klasy `id`, `occurred_at`, `payload`, `correlation_id`, `causation_id`, `published_at`) i `DeliveryOutboxRow` (kształt instancji). Konstruktor przyjmuje `session_factory`, `models` (jeden z `EventDeliveryModels | MessageDeliveryModels | CommandDeliveryModels`), `transport: DeliveryTransport`, `kind: DeliveryKind` oraz `batch_size: int = 100`.

Wykrywanie dialektu — `self._skip_locked = dialect_name not in ("sqlite",)` (na bazach niebędących SQLite włączany jest `FOR UPDATE SKIP LOCKED`).

`run_once() -> int`:

1. `select(outbox_model).where(published_at IS NULL).order_by(occurred_at).limit(batch_size)`, a gdy `_skip_locked` → `.with_for_update(skip_locked=True)` (równoległe relaye nie czekają na siebie i nie podbierają nawzajem wierszy);
2. brak wierszy → `return 0`;
3. buduje listę `DeliveryEnvelope` przez `_to_envelope(row)` — `delivery_type = getattr(row, f"{kind}_type")` (kolumna zależna od rodzaju: `event_type`/`message_type`/`command_type`);
4. dla każdego envelopa `await self._transport.deliver(envelope)` — `deliver()` rzuca przy nack/timeout (confirm mode), więc całość się nie uda;
5. dopiero po sukcesie wszystkich: `row.published_at = now` i `session.commit()`; zwraca liczbę przetworzonych wierszy.

`published_at` jest ustawiane wyłącznie po udanej publikacji — crash między deliver a mark skutkuje re-deliverem (at-least-once; inbox konsumenta jest idempotentny).

### Outbox-to-inbox relays (event/message/command)

Wspólna struktura w `EventOutboxToInboxRelay` (`.../messaging/event/event_outbox_to_inbox_relay.py`), `MessageOutboxToInboxRelay` (`.../messaging/message/message_outbox_to_inbox_relay.py`), `CommandOutboxToInboxRelay` (`.../messaging/command/command_outbox_to_inbox_relay.py`). Każdy ma protokoły `XOutboxModel`/`XOutboxRow` z kolumną typu (odpowiednio `event_type`, `message_type`, `command_type`), kolumną `published_at` oraz pozostałymi wspólnymi kolumnami.

Konstruktor przyjmuje `session_factory` (źródło), `models`/`target_models`, opcjonalny `target_session_factory` (gdy `None`, użyty zostaje `session_factory` — możliwe przetwarzanie między **dwoma różnymi** fabrykami sesji), `batch_size: int = 100`; `EventOutboxToInboxRelay` dodatkowo przyjmuje `downstream: EventPublisher | None`. Wykrywane: `_skip_locked` (nie-SQLite) oraz `_is_postgres` (`dialect_name == "postgresql"`).

`run_once() -> int` — **dwa session factory**:

1. w sesji źródłowej: SELECT jak wyżej (published_at IS NULL, ORDER BY occurred_at, LIMIT batch_size, opcjonalnie `with_for_update(skip_locked=True)`); brak wierszy → 0;
2. w sesji docelowej (`self._target_session_factory()`): batch insert do `target_inbox_model` z wartościami `{id, <kind>_type, occurred_at, payload, correlation_id, causation_id, received_at: now, processed_at: None}`, potem `target_session.commit()`;
3. w sesji źródłowej: `row.published_at = now` i `session.commit()`.

Kolejność commitów (najpierw target, potem źródło) oznacza, że wiersz docelowy jest trwały zanim rekord outbox zostanie oznaczony jako opublikowany; przy crashu w przerwie rekord źródłowy nie ma `published_at` i całość powtarza się, a dedup po ID czyni to nieszkodliwym.

Dedup przy insertach:

- PostgreSQL — `_batch_insert_postgres`: `pg_insert(target_inbox_model).values(values)` i `.on_conflict_do_nothing(index_elements=["id"])`; po wykonaniu ustawia `row.published_at = now` na obiektach ORM;
- SQLite — `_batch_insert_sqlite`: `sa.insert(target_inbox_model).values(values)` z `stmt.prefix_with("OR IGNORE")` (odpowiednik `ON CONFLICT DO NOTHING`).

Po `_batch_insert_*` iteracja ustawia `row.published_at = now` w sesji źródłowej.

## Kluczowe pliki

- `shell/platform/infrastructure/messaging/transport/outbox_to_transport_relay.py`
- `shell/platform/infrastructure/messaging/event/event_outbox_to_inbox_relay.py`
- `shell/platform/infrastructure/messaging/message/message_outbox_to_inbox_relay.py`
- `shell/platform/infrastructure/messaging/command/command_outbox_to_inbox_relay.py`
- `shell/platform/application/ports/delivery_transport.py`

## Powiązane koncepcje

- [transactional-outbox](transactional-outbox.md)
- [delivery-transport](delivery-transport.md)
- [inbox-lifecycle](inbox-lifecycle.md)
- [delivery-overview](delivery-overview.md)
- [delivery-models](delivery-models.md)
- [unit-of-work](unit-of-work.md)
