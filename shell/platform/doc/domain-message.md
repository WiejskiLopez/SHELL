# DomainMessage

## Cel / Co realizuje

`DomainMessage` (w `shell/platform/domain/messages/domain_message.py`) jest bazowym, frozen dataclass dla wiadomości domenowych — odpowiednik `DomainEvent`, ale identyfikowany przez `MessageId` zamiast `EventId`. Wiadomości są rejestrowane przez `AggregateRoot.append_message()` i odbierane przez `pull_messages()`.

## Problem

Oprócz zdarzeń domenowych (faktów o przeszłości) agregat może potrzebować wysyłać wiadomości, które nie są zdarzeniami w sensie event-sourcingu. Obie kategorie mają jednak wspólny zestaw metadanych (identyfikator, kontekst agregatu, czas, wersja schematu). Model potrzebuje spójnego nośnika tych metadanych, aby warstwa aplikacji mogła przetwarzać wiadomości w kontrolowany sposób (outbox, deduplikacja, korelacja).

## Realizacja techniczna

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class DomainMessage:
    message_id: MessageId = field(default_factory=MessageId.generate)
    aggregate_id: AggregateId = field(default_factory=lambda: AggregateId(""))
    aggregate_name: AggregateName = field(default_factory=lambda: AggregateName(""))
    occurred_at: OccurredAt
    schema_version: SchemaVersion = field(default_factory=lambda: SchemaVersion(1))
```

Struktura jest identyczna z `DomainEvent` poza typem identyfikatora:

- `message_id: MessageId` — unikalny identyfikator wiadomości; generowany przez `MessageId.generate()` (uuid4).
- `aggregate_id: AggregateId` — domyślnie `AggregateId("")`; nadpisywany przez `AggregateRoot.append_message()` (`object.__setattr__` ze względu na frozen dataclass) wartością `AggregateId(self.id.value if hasattr(self.id, "value") else str(self.id))`.
- `aggregate_name: AggregateName` — domyślnie `AggregateName("")`; nadpisywany jako `AggregateName(type(self).__name__)`.
- `occurred_at: OccurredAt` — pole wymagane (`kw_only=True`).
- `schema_version: SchemaVersion` — domyślnie `SchemaVersion(1)`.

Import `OccurredAt` w tym module ma adnotację `# noqa: TC001 -- needed at runtime for deserialization type resolution` — `OccurredAt` musi być dostępny w czasie wykonania (nie tylko dla typów) do rozwiązywania typów przy deserializacji.

Przepływ użycia: metody domenowe agregatu wywołują `append_message(DomainMessage...)`; warstwa aplikacji po udanej transakcji pobiera wiadomości przez `AggregateRoot.pull_messages()` i przekazuje je dalej (outbox / publisher).

## Kluczowe pliki

- `shell/platform/domain/messages/domain_message.py`
- `shell/platform/domain/base/aggregate_root.py`
- `shell/platform/domain/value_objects/message_id.py`
- `shell/platform/domain/value_objects/occurred_at.py`
- `shell/platform/domain/value_objects/schema_version.py`

## Powiązane koncepcje

- [aggregate-root](aggregate-root.md)
- [domain-event](domain-event.md)
- [entity-id](entity-id.md)
- [value-object](value-object.md)
- [transactional-outbox](transactional-outbox.md)
- [tracing-context](tracing-context.md)
