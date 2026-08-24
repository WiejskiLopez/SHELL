# AggregateRoot

## Cel / Co realizuje

`AggregateRoot` (klasa `AggregateRoot(Entity[TId])` w `shell/platform/domain/base/aggregate_root.py`) jest bazą dla wszystkich korzeni agregatów w bounded contexts. Rozszerza `Entity[TId]` o prywatny bufor zdarzeń domenowych rejestrowanych przez metody domenowe; warstwa aplikacji wywołuje `pull_events()` po udanej transakcji, aby przekazać je do publishera eventów / outbox.

## Problem

W DDD zmiany stanu agregatu muszą być eksponowane na zewnątrz jako zdarzenia domenowe, ale warstwa aplikacji nie może ich wyciągać bezpośrednio z wnętrza agregatu ani agregat nie może sam wysyłać zdarzeń (zależność od infrastruktury). Potrzebny jest mechanizm akumulacji zdarzeń wewnątrz agregatu i ich deterministycznego odbioru przez warstwę aplikacji w punkcie kontrolowanym (po commicie transakcji). Dodatkowo każde zdarzenie musi być jednoznacznie powiązane z agregatem, który je wyemitował.

## Realizacja techniczna

Klasa `AggregateRoot` dziedziczy po `Entity[TId]` (patrz [entity](entity.md)) i dodaje bufor zdarzeń:

```python
__slots__ = ("_events",)

_events: list[DomainEvent]

def __init__(self, id: TId) -> None:
    super().__init__(id)
    self._events = []
```

Rejestracja zdarzenia — `append_event(event: DomainEvent) -> None`:

- metoda importuje lokalnie `AggregateId` i `AggregateName` z `shell/platform/domain/value_objects/`;
- uzupełnia event o dane agregatu przez `object.__setattr__`, co jest konieczne, ponieważ `DomainEvent` jest frozen dataclass (brak normalnego settera):
  - `aggregate_id = AggregateId(self.id.value if hasattr(self.id, "value") else str(self.id))`,
  - `aggregate_name = AggregateName(type(self).__name__)` (nazwa klasy agregatu);
- dopisuje event do `self._events`.

Odbiór zdarzeń — `pull_events() -> list[DomainEvent]`:

- kopiuje bufor (`self._events.copy()`), czyści go (`self._events.clear()`) i zwraca kopię. Dzięki temu każde zdarzenie jest odbierane dokładnie raz przez warstwę aplikacji.

> Kanał Message (`append_message`/`pull_messages`) został usunięty — patrz `docs/messages-removed.md`.

Wzorzec metody domenowej (sekwencja guard → mutacja → event): metody domenowe agregatu najpierw wykonują guard clauses (weryfikacja invariants — patrz `DomainError` w [domain-errors](domain-errors.md)), następnie mutują stan prywatnych pól, a na końcu wywołują `append_event(...)`. Brak publicznych setterów — stan jest zmieniany wyłącznie przez metody domenowe; tożsamość jest ustawiana tylko w `__init__`.

## Kluczowe pliki

- `shell/platform/domain/base/aggregate_root.py`
- `shell/platform/domain/base/entity.py`
- `shell/platform/domain/events/domain_event.py`
- `shell/platform/domain/value_objects/aggregate_id.py`
- `shell/platform/domain/value_objects/aggregate_name.py`

## Powiązane koncepcje

- [entity](entity.md)
- [entity-id](entity-id.md)
- [domain-event](domain-event.md)
- [unit-of-work](unit-of-work.md)
- [cqrs-buses](cqrs-buses.md)
- [transactional-outbox](transactional-outbox.md)
- [sqlalchemy-persistence](sqlalchemy-persistence.md)
