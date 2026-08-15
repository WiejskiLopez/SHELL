# Transport dostaw (DeliveryTransport / EnvelopeCodec / RabbitMQ)

## Cel / Co realizuje

Port `DeliveryTransport` (w `shell/platform/application/ports/delivery_transport.py`) definiuje kontrakt przenoszenia zserializowanych rekordów delivery między bounded contexts. `EnvelopeCodec` (`shell/platform/infrastructure/messaging/transport/envelope_codec.py`) konwertuje `DeliveryEnvelope` do/ze spłaszczonego JSON-a (format wire). Adaptery RabbitMQ realizują ten port: `RabbitDeliveryTransport` publikuje koperty na broker, a `RabbitInboxConsumer` subskrybuje koperty z brokera i zapisuje je idempotentnie do lokalnego inbox.

## Problem

Dostawy (eventy, wiadomości, komendy) muszą trafić z produkującego BC do konsumujących BC w sposób niezależny od konkretnego brokera (hexagonalna architektura — domena/aplikacja nie znają RabbitMQ). Trzeba zdefiniować wspólny kształt danych (`DeliveryEnvelope`), jednoznaczny format bajtowy na brokera (JSON), konwencję routingu (exchange/topic, routing key per typ) oraz symetryczne adaptery: producenta (publish z potwierdzeniem) i konsumenta (at-least-once, idempotentny insert do inbox, ack dopiero po trwałym zapisie).

## Realizacja techniczna

### Port i model

W `shell/platform/application/ports/delivery_transport.py`:

- `DeliveryKind = Literal["event", "message", "command"]`;
- `DeliveryEnvelope` (frozen dataclass): `kind: DeliveryKind`, `delivery_id: str`, `delivery_type: str`, `occurred_at: datetime`, `payload: dict[str, object]`, `correlation_id: str`, `causation_id: str`;
- `DeliveryTransport(Protocol)` z jedną metodą: `async def deliver(self, envelope: DeliveryEnvelope) -> None`.

### EnvelopeCodec

`EnvelopeCodec` (w `envelope_codec.py`) — format wire to spłaszczony obiekt JSON `{kind, delivery_id, delivery_type, occurred_at, payload, correlation_id, causation_id}`:

- `encode(envelope) -> bytes` — `occurred_at` przez `isoformat()`, `json.dumps(document, separators=(",", ":"))` kodowane UTF-8;
- `decode(raw) -> bytes` — walidacja `kind in ("event", "message", "command")`, przy nieznanym kind podnosi `ValueError`; `payload` fallback na `{}` gdy pusty; `occurred_at` parsowany przez `_parse_occurred_at` (uzupełnia brak strefy czasowej do `UTC` i normalizuje `astimezone(UTC)`).

### RabitDeliveryTransport (producent)

`RabbitDeliveryTransport` (`shell/platform/infrastructure/messaging/transport/rabbit/rabbit_delivery_transport.py`):

- stała `EXCHANGE_NAME = "shell.delivery"`; konstruktor z `url`, `exchange_name`, `publisher_confirms: bool = True`;
- `deliver(envelope) -> None` — pobiera exchange i publikuje `Message(body=codec.encode(envelope), delivery_mode=DeliveryMode.PERSISTENT, content_type="application/json")` z routing key `f"{envelope.kind}.{envelope.delivery_type}"` (np. `event.TaskExecutionCreatedEvent`) i `mandatory=False`;
- `_get_channel()` — leniwe łączenie pod `asyncio.Lock`: `connect_robust(url, timeout=30)`, kanał z `publisher_confirms`, deklaracja exchange `type="topic"`, `durable=True`;
- publikacja jest confirm-based — nack/timeout rzuca wyjątkiem, więc caller (relay outbox) może wykonać retry i nie zgubić rekordu;
- `close()` — zamyka kanał i połączenie.

### RabbitInboxConsumer (konsument)

`RabbitInboxConsumer` (`shell/platform/infrastructure/messaging/transport/rabbit/rabbit_inbox_consumer.py`):

- konstruktor: `url`, `session_factory`, `models` (jeden z `EventDeliveryModels | MessageDeliveryModels | CommandDeliveryModels`), `queue_name`, `routing_keys: list[str] | None = None` (domyślnie `["#"]`), `exchange_name = "shell.delivery"`;
- `start()` — `connect_robust`, kanał, `set_qos(prefetch_count=10)`, deklaracja exchange topic durable, deklaracja durable queue, dla każdego `routing_key` `await queue.bind(exchange, routing_key=routing_key)`, potem `queue.consume(self._on_message)`; konsument BC wiąże własną kolejkę z kluczami, które obsługuje;
- `_on_message(message)` — najpierw `self._codec.decode(message.body)`; błąd dekodowania (`ValueError/KeyError/TypeError`) → `await message.reject(requeue=False)` (zatruta wiadomość nie blokuje kolejki); potem `_persist(envelope)` — sukces → `await message.ack()`, porażka → `reject(requeue=False)`;
- `_persist(envelope) -> bool` — buduje kolumnę typu jako `f"{envelope.kind}_type"`, wartości `{id, type, occurred_at, payload, correlation_id, causation_id, received_at, status: PENDING}`, wykonuje `pg_insert(self._inbox_model).values(**values).on_conflict_do_nothing()` (idempotentny insert), `commit()`; wyjątek → log `Failed to persist inbox delivery`, zwraca `False`;
- ack następuje dopiero po trwałym zapisie — crash między insertem a ackiem redeliveruje wiadomość, którą idempotentny insert czyni nieszkodliwą (at-least-once).

## Kluczowe pliki

- `shell/platform/application/ports/delivery_transport.py`
- `shell/platform/infrastructure/messaging/transport/envelope_codec.py`
- `shell/platform/infrastructure/messaging/transport/rabbit/rabbit_delivery_transport.py`
- `shell/platform/infrastructure/messaging/transport/rabbit/rabbit_inbox_consumer.py`

## Powiązane koncepcje

- [relay](relay.md)
- [delivery-overview](delivery-overview.md)
- [transactional-outbox](transactional-outbox.md)
- [inbox-lifecycle](inbox-lifecycle.md)
- [envelope-versioning](envelope-versioning.md)
- [integration-contracts](integration-contracts.md)
- [ports-and-adapters](ports-and-adapters.md)
