# Relay outbox (OutboxToTransportRelay i outbox-to-inbox relays)

## Cel / Co realizuje

`OutboxToTransportRelay` (w `shell/platform/infrastructure/messaging/transport/outbox_to_transport_relay.py`) jest jedynym mostem producenta między transactional outbox a brokerem: czyta niepublikowane wiersze `outbox_*`, buduje kopertę i publikuje ją przez `DeliveryTransport`.

## Problem

Transactional outbox gwarantuje atomowość zapisu domeny i rekordu outbox, ale nie przenosi danych na broker ani do docelowego BC. Wspólny relay publikuje oczekujące wiersze, a brokerowy consumer zapisuje je do lokalnego inboxa. Idempotencja opiera się na `source_service` i `outbox_id`; lokalny inbox posiada własne `id`.

## Realizacja techniczna

### OutboxToTransportRelay (producent outbox → broker)

Protokoły `DeliveryOutboxModel` (kolumny klasy `id`, `occurred_at`, `payload`, `correlation_id`, `causation_id`, `published_at`) i `DeliveryOutboxRow` (kształt instancji). Konstruktor przyjmuje `session_factory`, `models` (jeden z `EventDeliveryModels | MessageDeliveryModels | CommandDeliveryModels`), `transport: DeliveryTransport`, `kind: DeliveryKind` oraz `batch_size: int = 100`.

Wykrywanie dialektu — `self._skip_locked = dialect_name not in ("sqlite",)` (na bazach niebędących SQLite włączany jest `FOR UPDATE SKIP LOCKED`).

`run_once() -> int`:

1. `select(outbox_model).where(published_at IS NULL).order_by(occurred_at).limit(batch_size)`, a gdy `_skip_locked` → `.with_for_update(skip_locked=True)` (równoległe relaye nie czekają na siebie i nie podbierają nawzajem wierszy);
2. brak wierszy → `return 0`;
3. buduje listę `DeliveryEnvelope` przez `_to_envelope(row)` — `contract_type = getattr(row, f"{kind}_type")` (kolumna zależna od rodzaju: `event_type`/`message_type`/`command_type`), a `outbox_id` pochodzi z `outbox.id`;
4. dla każdego envelopa `await self._transport.deliver(envelope)` — `deliver()` rzuca przy nack/timeout (confirm mode), więc całość się nie uda;
5. dopiero po sukcesie wszystkich: `row.published_at = now` i `session.commit()`; zwraca liczbę przetworzonych wierszy.

`published_at` jest ustawiane wyłącznie po udanej publikacji — crash między deliver a mark skutkuje re-deliverem (at-least-once; inbox konsumenta jest idempotentny).

## Kluczowe pliki

- `shell/platform/infrastructure/messaging/transport/outbox_to_transport_relay.py`
- `shell/platform/application/ports/delivery_transport.py`

## Powiązane koncepcje

- [transactional-outbox](transactional-outbox.md)
- [delivery-transport](delivery-transport.md)
- [inbox-lifecycle](inbox-lifecycle.md)
- [delivery-overview](delivery-overview.md)
- [delivery-models](delivery-models.md)
- [unit-of-work](unit-of-work.md)
