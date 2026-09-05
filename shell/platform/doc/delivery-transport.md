# Transport dostaw (DeliveryTransport / EnvelopeCodec / RabbitMQ)

## Cel / Co realizuje

Porty `IntegrationEventDeliveryTransport` i `CommandDeliveryTransport` (w `shell/platform/application/ports/transport/`) definiują kontrakt przenoszenia zserializowanych rekordów delivery między bounded contexts. `EnvelopeCodec` (w `shell/platform/infrastructure/messaging/event_transport/envelope_codec.py` oraz `command_transport/envelope_codec.py`) konwertuje koperty do/ze spłaszczonego JSON-a (format wire). Adaptery RabbitMQ realizują porty: `RabbitEventDeliveryTransport`/`RabbitCommandDeliveryTransport` publikują koperty na broker, a `EventInboxConsumer`/`CommandInboxConsumer` subskrybują koperty z brokera i zapisują je idempotentnie do lokalnego inbox.

## Problem

Dostawy (eventy, komendy) muszą trafić z produkującego BC do konsumujących BC w sposób niezależny od konkretnego brokera (hexagonalna architektura — domena/aplikacja nie znają RabbitMQ). Trzeba zdefiniować wspólny kształt danych (koperta), jednoznaczny format bajtowy na brokera (JSON), konwencję routingu (exchange/topic, routing key per typ) oraz symetryczne adaptery: producenta (publish z potwierdzeniem) i konsumenta (at-least-once, idempotentny insert do inbox, ack dopiero po trwałym zapisie).

## Realizacja techniczna

### Porty i koperty

W `shell/platform/application/ports/transport/`:

- `event_transport.py` — `EventDeliveryEnvelope` i port `IntegrationEventDeliveryTransport`;
- `command_transport.py` — `CommandDeliveryEnvelope` i port `CommandDeliveryTransport`.

### EnvelopeCodec

`EnvelopeCodec` — format wire to spłaszczony obiekt JSON **bez `kind` i `outbox_id`** (kanał wynika z typu koperty). Event (`event_transport/envelope_codec.py`): `{contract_type, occurred_at, schema_version, payload, correlation_id, causation_id, event_id, source_service, destination_service, aggregate_id}`. Command (`command_transport/envelope_codec.py`): `{command_id, contract_type, source_service, destination_service, issued_at, schema_version, payload, correlation_id, causation_id}`.

- `encode(envelope) -> bytes` — timestamp przez `isoformat()`, `json.dumps(document, separators=(",", ":"))` kodowane UTF-8;
- `decode(raw)` — parsuje JSON i odtwarza kopertę; brak jawnej walidacji `kind` (nie istnieje na wire).

### Rabbit*DeliveryTransport (producent)

`RabbitEventDeliveryTransport` / `RabbitCommandDeliveryTransport` (`messaging/event_transport/rabbit/`, `messaging/command_transport/rabbit/`):

- stała `EXCHANGE_NAME = "shell.delivery"`; konstruktor z `url`, `exchange_name`, `publisher_confirms: bool = True`;
- `deliver(envelope)` — pobiera exchange i publikuje JSON envelope z routing key `event.<contract_type>` (event) lub `command.<destination_service>.<contract_type>` (command), `DeliveryMode.PERSISTENT`, `mandatory=True`;
- `_get_channel()` — leniwe łączenie pod `asyncio.Lock`: `connect_robust(url, timeout=30)`, kanał z `publisher_confirms` i `on_return_raises`, deklaracja exchange `type="topic"`, `durable=True`;
- publikacja jest confirm-based — nack/timeout rzuca wyjątkiem, więc caller (relay outbox) może wykonać retry i nie zgubić rekordu;
- `close()` — zamyka kanał i połączenie.

### InboxConsumer (konsument)

`EventInboxConsumer` (`messaging/event/event_inbox_consumer.py`) i `CommandInboxConsumer` (`messaging/command/command_inbox_consumer.py`):

- konstruktor: `url`, `session_factory`, właściwy bundle modeli (`EventDeliveryModels` albo `CommandDeliveryModels`), `queue_name` (event) / `service_name` (command; kolejka `shell-<service>-command-inbox`), opcjonalnie `routing_keys` (event — domyślnie `["event.#"]`), `exchange_name`;
- `start()` — `connect_robust`, kanał, `set_qos(prefetch_count=10)`, deklaracja exchange topic durable, deklaracja durable queue, bind: event do każdego `routing_key`, command do `command.<service>.#`; potem `queue.consume(self._on_message)`;
- `_on_message(message)` — najpierw `self._codec.decode(message.body)`; błąd dekodowania (`ValueError/KeyError/TypeError`) → `await message.reject(requeue=False)` (zatruta wiadomość nie blokuje kolejki); potem `_persist(envelope)` — błąd zapisu → `reject(requeue=True)`, sukces → `await message.ack()`;
- `_persist(envelope)` — generuje lokalne `inbox.id` (`_id_generator.new_id()`), zapisuje `event_id`/`command_id`, `source_service`, typ kontraktu (`integration_event_name`/`command_name`), `schema_version`, `received_at`, payload, `correlation_id`/`causation_id` i wykonuje idempotentny insert `pg_insert(...).on_conflict_do_nothing()` oraz commit;
- ack następuje dopiero po trwałym zapisie — lokalne `inbox.id` identyfikuje rekord odbiorcy; dedup po `(source_service, event_id|command_id)`.

## Kluczowe pliki

- `shell/platform/application/ports/transport/event_transport.py`
- `shell/platform/application/ports/transport/command_transport.py`
- `shell/platform/infrastructure/messaging/event_transport/envelope_codec.py`
- `shell/platform/infrastructure/messaging/command_transport/envelope_codec.py`
- `shell/platform/infrastructure/messaging/event_transport/rabbit/rabbit_event_delivery_transport.py`
- `shell/platform/infrastructure/messaging/command_transport/rabbit/rabbit_command_delivery_transport.py`
- `shell/platform/infrastructure/messaging/event/event_inbox_consumer.py`
- `shell/platform/infrastructure/messaging/command/command_inbox_consumer.py`

## Powiązane koncepcje

- [relay](relay.md)
- [delivery-overview](delivery-overview.md)
- [transactional-outbox](transactional-outbox.md)
- [inbox-lifecycle](inbox-lifecycle.md)
- [envelope-versioning](envelope-versioning.md)
- [integration-contracts](integration-contracts.md)
- [ports-and-adapters](ports-and-adapters.md)