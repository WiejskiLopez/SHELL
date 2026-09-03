# Warstwa domenowa

Reguły budowy klocków domenowych. Warstwa `domain/` jest sercem systemu — czysty Python, bez zależności zewnętrznych.

## Struktura katalogu domeny

SHELL nie ma top-level pakietu `shell/domain`. Domena żyje per BC: `shell/<service>/domain/<bc>/...`, a platforma domenowa w `shell/platform/domain/...`.

```
shell/<service>/domain/<bc>/
├── aggregates/<agregat>/     # Aggregate Root
│   ├── <agregat>.py
│   ├── entities/             # Child entities
│   ├── events/               # Domain Events
│   ├── repositories/         # Porty repozytoriów (własna persystencja)
│   ├── ports/                # Porty zewnętrzne — odczyt (Provider) i operacje (Command Port)
│   ├── services/             # Domain Services
│   ├── exceptions/           # Domain Exceptions (_error.py)
│   └── value_objects/        # Value Objects (w tym ID)
├── entities/                 # Encje współdzielone miedzy <agregat> tego <bc> (jeśli BC wymaga)
├── value_objects/            # VO BC współdzielone miedzy <agregat> tego <bc> (jeśli BC wymaga)
└── services/                 # Domain Services współdzielone miedzy <agregat> tego <bc>
```

> Platforma domenowa żyje osobno w `shell/platform/domain/` (base klasy w `base/`, `value_objects/`, `ports/`, `events/`, `exceptions/`) — nie jest katalogiem żadnego BC.

## Kluczowe reguły

### Aggregate Root
- Dziedziczy po `AggregateRoot[TId]` z `shell/platform/domain/base/aggregate_root.py`
- **Nie używa `@dataclass`** — tożsamość to nie równość strukturalna
- Obowiązkowo `__slots__` (bez powtarzania `_id` z base class)
- `__eq__` i `__hash__` bazują wyłącznie na ID
- Stan modyfikowalny wyłącznie przez metody domenowe
- Żadnych publicznych setterów
- Każda metoda mutująca: guard clause → mutacja → `append_event()` (bezwarunkowo dla przejść stanu)
- Referencje do innych agregatów wyłącznie przez ID (nigdy obiekty)
- Jeden agregat = jedna transakcja

### Entity
- Dziedziczy po `Entity[TId]`
- **Nie używa `@dataclass`**
- Obowiązkowo `__slots__`
- Child entity: ma lokalną tożsamość tylko w kontekście rodzica
- Modyfikowana wyłącznie przez metody Aggregate Root
- Repozytorium nalezy do Aggregate Root
- Kod domenowy korzysta z czystych typow domenowych

### Value Object
- Dziedziczy po `ValueObject` z `shell.platform.domain.base.value_object`
- `@dataclass(frozen=True, slots=True)` dla VO opartych na pojedynczej wartości
- `@dataclass(frozen=True)` dla VO złożonych
- Walidacja w `__post_init__`, rzuca dedykowany `DomainError`
- Zawiera zachowania biznesowe (nie tylko dane)
- Factory methods (`generate()`, `now()`, `initial()`, `of()`, `from_string()`)
- Każde ID w domenie to osobny VO (dziedziczy po `EntityId`)
- Sygnatury w warstwie domenowej używają VO, nigdy typów prostych

### Domain Event
- `@dataclass(frozen=True, slots=True)`
- Rozszerza `DomainEvent` (base class z metadanymi: `event_id`, `aggregate_id`, `occurred_at` — wszystkie jako ValueObjecty platformy)
- Payload zawiera tylko fakty (co się stało), nigdy instrukcje (co ma się stać)
- Nazwa w czasie przeszłym dokonanym: `<AggregateName><PastVerb>Event`
- Ewolucję schematu obsługuje `IntegrationEventDeserializer` + upcaster po stronie outbox/inbox; metadane koperty (`schema_version`, `correlation_id`, `causation_id`, `integration_event_name`) nie są polami klasy domenowej

### Repository Port
- Protocol w `shell/<service>/domain/<bc>/aggregates/<agregat>/repositories/`
- Rozszerza `RepositoryPort` z `shell/platform/domain/ports/repository_port.py` (kontrakt: `get_by_id`, `save`, `delete`, `exists`)
- Może dodawać metody `list_by_*()` specyficzne dla agregatu
- Operuje na typach domenowych (agregaty, VO)
- Nie używa `store()`, `persist()`, `add()`, `update()` — tylko `save()`

### Domain Service
- Stateless, bez własnego stanu/tożsamości
- Używany gdy logika operuje na wielu agregatach tego samego BC
- Może używać innych Domain Services
- Porty (Protocol) dla zależności zewnętrznych
- Wstrzykiwany przez DI (bywa jako Factory per użycie)

### Domain Exception
- Dziedziczy po `DomainError` z `shell/platform/domain/exceptions/domain_error.py`
- Każdy invariant ma dedykowaną klasę wyjątku (`<Aggregate><Problem>Error`, plik `<nazwa>_error.py`)
- Nigdy ogólny `ValueError` czy `RuntimeError` dla reguł biznesowych

### Zakazy w warstwie domenowej
- Nie importuje: `sqlalchemy`, `pydantic`, `fastapi`, `motor`
- Nie importuje: `shell.*.application.*`, `shell.*.infrastructure.*`, `shell.*.framework.*`, `shell.*.bootstrap.*`
- Encje/Aggregaty nie używają `@dataclass`
- Brak publicznych setterów dla stanu domenowego
- Brak referencji obiektowych do innych agregatów (tylko ID)

## Powiązane skille

- `platform/domain-layer/aggregate-design/SKILL.md` — projektowanie agregatów
- `platform/domain-layer/entity/SKILL.md` — projektowanie encji
- `platform/domain-layer/domain-event/SKILL.md` — projektowanie eventów
- `platform/domain-layer/domain-service/SKILL.md` — Domain Services
- `platform/domain-layer/domain-invariant/SKILL.md` — invarianty biznesowe
- `platform/domain-layer/factory/SKILL.md` — factory pattern
- `platform/domain-layer/specification/SKILL.md` — specification pattern