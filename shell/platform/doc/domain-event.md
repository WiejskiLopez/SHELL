# DomainEvent

## Cel / Co realizuje

`DomainEvent` (w `shell/platform/domain/events/domain_event.py`) jest bazowym, frozen dataclass dla wszystkich zdarzeń domenowych. Reprezentuje fakt, który już nastąpił w agregacie, wraz z metadanymi korelacyjnymi: `event_id`, `aggregate_id`, `aggregate_name`, `occurred_at`, `schema_version`. Zdarzenia są rejestrowane przez `AggregateRoot.append_event()` i odbierane przez `pull_events()` po udanej transakcji.

## Problem

Zmiany stanu agregatu muszą być komunikowane poza granice transakcji (outbox, innym bounded contexts) jako niezmienne, kompletne fakty. Każde zdarzenie potrzebuje: unikalnego identyfikatora, kontekstu agregatu (id i nazwa klasy), czasu wystąpienia oraz wersji schematu (do wersjonowania kontraktu). Brak tych metadanych uniemożliwia deduplikację, korelację i migrację schematów.

## Realizacja techniczna

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    event_id: EventId = field(default_factory=EventId.generate)
    aggregate_id: AggregateId = field(default_factory=lambda: AggregateId(""))
    aggregate_name: AggregateName = field(default_factory=lambda: AggregateName(""))
    occurred_at: OccurredAt
    schema_version: SchemaVersion = field(default_factory=lambda: SchemaVersion(1))
```

Pola:

- `event_id: EventId` — unikalny identyfikator eventu; generowany automatycznie przez `EventId.generate()` (uuid4).
- `aggregate_id: AggregateId` — domyślnie puste `AggregateId("")`; nadpisywane przez `AggregateRoot.append_event()` (frozen dataclass wymusza `object.__setattr__`) wartością `AggregateId(self.id.value if hasattr(self.id, "value") else str(self.id))`.
- `aggregate_name: AggregateName` — domyślnie `AggregateName("")`; nadpisywane jako `AggregateName(type(self).__name__)` (nazwa klasy agregatu).
- `occurred_at: OccurredAt` — pole wymagane (`kw_only=True`), czas wystąpienia zdarzenia.
- `schema_version: SchemaVersion` — domyślnie `SchemaVersion(1)`; używane przy wersjonowaniu i upcastingu kontraktów.

`kw_only=True` wymusza przekazywanie pól po nazwie; `frozen=True, slots=True` daje niezmienność i optymalizację pamięci. Zdarzenia są konfigurowane wyłącznie przez fabryki i metody domenowe agregatu — brak publicznych setterów.

Wbudowane zdarzenia systemowe:

- `AggregateDeletedEvent` (`shell/platform/domain/events/aggregate_deleted_event.py`) — emitowany przy miękkim usunięciu agregatu. Rozszerza `DomainEvent` o pole `deleted_at: DeletedAt`. Fabryka:
  ```python
  @classmethod
  def now(cls, deleted_at: DeletedAt) -> AggregateDeletedEvent:
      return cls(
          occurred_at=OccurredAt.from_datetime(deleted_at.value),
          deleted_at=deleted_at,
      )
  ```
  Czas zdarzenia (`occurred_at`) pochodzi z `deleted_at.value` przez `OccurredAt.from_datetime`.
- `AggregateRestoredEvent` (`shell/platform/domain/events/aggregate_restored_event.py`) — emitowany przy przywróceniu miękkiego usunięcia. Rozszerza `DomainEvent` bez dodatkowych pól. Fabryka:
  ```python
  @classmethod
  def now(cls, now: OccurredAt) -> AggregateRestoredEvent:
      return cls(occurred_at=now)
  ```

Konwencja nazw: konkretne eventy biznesowe (np. `OrderPlaced`) dziedziczą po `DomainEvent` jako `@dataclass(frozen=True, slots=True)`, dodają pola biznesowe i fabrykę `now(...)`.

## Kluczowe pliki

- `shell/platform/domain/events/domain_event.py`
- `shell/platform/domain/events/aggregate_deleted_event.py`
- `shell/platform/domain/events/aggregate_restored_event.py`
- `shell/platform/domain/base/aggregate_root.py`
- `shell/platform/domain/value_objects/event_id.py`
- `shell/platform/domain/value_objects/occurred_at.py`
- `shell/platform/domain/value_objects/schema_version.py`
- `shell/platform/domain/value_objects/deleted_at.py`

## Powiązane koncepcje

- [aggregate-root](aggregate-root.md)
- [domain-message](domain-message.md)
- [entity-id](entity-id.md)
- [value-object](value-object.md)
- [transactional-outbox](transactional-outbox.md)
- [tracing-context](tracing-context.md)
- [envelope-versioning](envelope-versioning.md)
- [contract-catalog](contract-catalog.md)
