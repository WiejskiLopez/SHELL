# DomainEvent

## Cel / Co realizuje

`DomainEvent` (w `shell/platform/domain/events/domain_event.py`) jest bazowym, frozen dataclass dla wszystkich zdarzeń domenowych. Reprezentuje fakt, który już nastąpił w agregacie, wraz z metadanymi korelacyjnymi: `event_id`, `aggregate_id`, `occurred_at`. Zdarzenia są rejestrowane przez `AggregateRoot.append_event()` i odbierane przez `pull_events()` po udanej transakcji.

## Problem

Zmiany stanu agregatu muszą być komunikowane poza granice transakcji (outbox, innym bounded contexts) jako niezmienne, kompletne fakty. Każde zdarzenie potrzebuje: unikalnego identyfikatora, kontekstu agregatu (id) oraz czasu wystąpienia. Brak tych metadanych uniemożliwia deduplikację i korelację. Wersja schematu (`schema_version`) jest nadawana dopiero na granicy kontraktu integracyjnego (mapper → `IntegrationEvent`), nie w zdarzeniu domenowym.

## Realizacja techniczna

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    event_id: EventId = field(default_factory=EventId.generate)
    aggregate_id: AggregateId = field(default_factory=AggregateId.generate)
    occurred_at: OccurredAt
```

Pola:

- `event_id: EventId` — unikalny identyfikator eventu; generowany automatycznie przez `EventId.generate()` (uuid4).
- `aggregate_id: AggregateId` — identyfikator agregatu; domyślnie generowany, nadpisywany przez `AggregateRoot.append_event()` (frozen dataclass wymusza `object.__setattr__`) wartością `AggregateId(self.id.value if hasattr(self.id, "value") else str(self.id))`.
- `occurred_at: OccurredAt` — pole wymagane (`kw_only=True`), czas wystąpienia zdarzenia.

`kw_only=True` wymusza przekazywanie pól po nazwie; `frozen=True, slots=True` daje niezmienność i optymalizację pamięci. Zdarzenia są konfigurowane wyłącznie przez fabryki i metody domenowe agregatu — brak publicznych setterów.

Wbudowane zdarzenia systemowe:

- `AggregateDeletedEvent` (`shell/platform/domain/events/aggregate_deleted_event.py`) — emitowany przy miękkim usunięciu agregatu. Nie dodaje własnych pól; fabryka przyjmuje czas jako `OccurredAt`:
  ```python
  @classmethod
  def now(cls, deleted_at: OccurredAt) -> AggregateDeletedEvent:
      return cls(occurred_at=deleted_at)
  ```
- `AggregateRestoredEvent` (`shell/platform/domain/events/aggregate_restored_event.py`) — emitowany przy przywróceniu miękkiego usunięcia. Rozszerza `DomainEvent` bez dodatkowych pól. Fabryka:
  ```python
  @classmethod
  def now(cls, now: OccurredAt) -> AggregateRestoredEvent:
      return cls(occurred_at=now)
  ```

Konwencja nazw: konkretne eventy biznesowe (np. `UserCreatedEvent`) dziedziczą po `DomainEvent` jako `@dataclass(frozen=True, slots=True)`, dodają pola biznesowe i fabrykę `now(...)`.

## Kluczowe pliki

- `shell/platform/domain/events/domain_event.py`
- `shell/platform/domain/events/aggregate_deleted_event.py`
- `shell/platform/domain/events/aggregate_restored_event.py`
- `shell/platform/domain/base/aggregate_root.py`
- `shell/platform/domain/value_objects/event_id.py`
- `shell/platform/domain/value_objects/occurred_at.py`
- `shell/platform/domain/value_objects/aggregate_id.py`

## Powiązane koncepcje

- [aggregate-root](aggregate-root.md)
- [entity-id](entity-id.md)
- [value-object](value-object.md)
- [transactional-outbox](transactional-outbox.md)
- [tracing-context](tracing-context.md)
- [integration-contracts](integration-contracts.md)
- [contract-catalog](contract-catalog.md)