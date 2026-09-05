# Relay outbox (EventOutboxRelay i CommandOutboxRelay)

## Cel / Co realizuje

Relay'e są mostem producenta między transactional outbox a brokerem: czytają niepublikowane
wiersze outboxa, budują kopertę i publikują ją przez transport. `EventOutboxRelay`
(`messaging/event/event_outbox_relay.py`) obsługuje `event_outbox`, `CommandOutboxRelay`
(`messaging/command/command_outbox_relay.py`) obsługuje `command_outbox`. Wspólny cykl
publikacji żyje w bazie `OutboxRelayBase` (`messaging/delivery/outbox_relay_base.py`).

## Problem

Transactional outbox gwarantuje atomowość zapisu domeny i rekordu outbox, ale nie przenosi
danych na broker ani do docelowego BC. Relay publikuje oczekujące wiersze, a brokerowy
consumer zapisuje je do lokalnego inboxa. Idempotencja opiera się na `source_service`
i logicznym ID (`event_id`/`command_id`); lokalny inbox posiada własne `id`.

## Realizacja techniczna

### OutboxRelayBase (wspólny cykl publikacji)

Konstruktor przyjmuje `session_factory`, transport oraz `batch_size: int = 100`.
Wykrywanie dialektu — `self._skip_locked = dialect_name not in ("sqlite",)` (na bazach
niebędących SQLite włączany jest `FOR UPDATE SKIP LOCKED`).

Podklasy dostarczają: `outbox_model`, `order_column` (event: `occurred_at`; command:
`issued_at`) oraz `_to_envelope(row)`.

`run_once() -> int`:

1. `select(outbox_model).where(published_at IS NULL).order_by(order_column).limit(batch_size)`,
   a gdy `_skip_locked` → `.with_for_update(skip_locked=True)` (równoległe relaye nie czekają
   na siebie i nie podbierają nawzajem wierszy);
2. brak wierszy → `return 0`;
3. buduje właściwą kopertę przez `_to_envelope(row)` — `contract_type` z
   `integration_event_name`/`command_name`, `destination_service` z `target_service`
   (eventy: `"*"` fan-out); koperta nie zawiera `outbox_id`;
4. dla każdego envelopa `await self._transport.deliver(envelope)` — `deliver()` rzuca przy
   nack/timeout (confirm mode), więc całość się nie uda;
5. dopiero po sukcesie wszystkich: `row.published_at = now` i `session.commit()`; zwraca
   liczbę przetworzonych wierszy.

`published_at` jest ustawiane wyłącznie po udanej publikacji — crash między deliver a mark
skutkuje re-deliverem (at-least-once; inbox konsumenta jest idempotentny).

## Kluczowe pliki

- `shell/platform/infrastructure/messaging/delivery/outbox_relay_base.py` (OutboxRelayBase)
- `shell/platform/infrastructure/messaging/event/event_outbox_relay.py` (EventOutboxRelay)
- `shell/platform/infrastructure/messaging/command/command_outbox_relay.py` (CommandOutboxRelay)
- `shell/platform/application/ports/transport/{event,command}_transport.py` (koperty + porty)

## Powiązane koncepcje

- [transactional-outbox](transactional-outbox.md)
- [delivery-transport](delivery-transport.md)
- [inbox-lifecycle](inbox-lifecycle.md)
- [delivery-overview](delivery-overview.md)
- [delivery-models](delivery-models.md)
- [unit-of-work](unit-of-work.md)