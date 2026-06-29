# Warstwa domenowa

Reguły budowy klocków domenowych. Warstwa `domain/` jest sercem systemu — czysty Python, bez zależności zewnętrznych.

## Struktura katalogu domeny

```
shell/domain/
├── <bc>/                         # Bounded Context
│   ├── aggregates/<agregat>/     # Aggregate Root
│   │   ├── <agregat>.py
│   │   ├── entities/             # Child entities
│   │   ├── events/               # Domain Events
│   |   ├── repositories/         # Porty repozytoriów
│   |   ├── ports/                # Porty serwisow innych aggregatow, a ich adaptery beda w infrastrukturze
|   │   ├── services/             # Domain Services
|   │   ├── specifications/       # Specification classes
|   │   ├── exceptions/           # Domain Exceptions
|   │   ├── rules/                # Rule Objects
|   │   ├── politics/             # polityki agregatu
│   │   ├── factories/                # Factory classes współdzielone miedzy <agregat>
│   │   └── value_objects/        # Value Objects (w tym ID)
│   ├── entities/                 # Encje współdzielone miedzy <agregat> tego <bc>
│   ├── value_objects/            # VO BC współdzielone miedzy <agregat> tego <bc>
│   └── services/                 # Domain Services współdzielone miedzy <agregat> tego <bc>
├── platform/                     # Uniwersalne elementy platformy
│   ├── value_objects/            # VO uniwersalne (Version, Timestamp itp.)
│   ├── entities/base/            # Entity, AggregateRoot base classes
│   ├── ports/                    # Porty uniwersalne (Clock, IdGenerator)
│   ├── base/                     # ValueObject, Specification base
│   ├── events/                   # DomainEvent base class
│   └── exceptions.py             # DomainError base
```

## Kluczowe reguły

### Aggregate Root
- Dziedziczy po `AggregateRoot[TId]` z `shell.domain.platform.entities.base.aggregate_root`
- **Nie używa `@dataclass`** — tożsamość to nie równość strukturalna
- Obowiązkowo `__slots__` (bez powtarzania `_id` z base class)
- `__eq__` i `__hash__` bazują wyłącznie na ID
- Stan modyfikowalny wyłącznie przez metody domenowe
- Żadnych publicznych setterów
- Każda metoda mutująca: guard clause → mutacja → `append_event()` (bezwarunkowo dla przejść stanu)
- Referencje do innych agregatów wyłącznie przez ID (nigdy obiekty)
- Jeden agregat = jedna transakcja
- Optymistyczne blokowanie przez `_version`

### Entity
- Dziedziczy po `Entity[TId]`
- **Nie używa `@dataclass`**
- Obowiązkowo `__slots__`
- Child entity: ma lokalną tożsamość tylko w kontekście rodzica
- Modyfikowana wyłącznie przez metody Aggregate Root
- Nie ma własnego repozytorium
- Brak importów ORM/infrastruktury

### Value Object
- Dziedziczy po `ValueObject` z `shell.domain.platform.base.value_object`
- `@dataclass(frozen=True, slots=True)` dla VO opartych na pojedynczej wartości
- `@dataclass(frozen=True)` dla VO złożonych
- Walidacja w `__post_init__`, rzuca `ValueError`
- Zawiera zachowania biznesowe (nie tylko dane)
- Factory methods (`generate()`, `now()`, `initial()`, `of()`, `from_string()`)
- Każde ID w domenie to osobny VO
- Sygnatury w warstwie domenowej używają VO, nigdy typów prostych

### Domain Event
- `@dataclass(frozen=True)`
- Rozszerza `DomainEvent` (base class z metadanymi: `event_id`, `aggregate_id`, `aggregate_type`, `occurred_at`, `correlation_id`, `causation_id`, `schema_version`)
- Payload zawiera tylko fakty (co się stało), nigdy instrukcje (co ma się stać)
- Nazwa w czasie przeszłym dokonanym: `<AggregateName><PastVerb>Event`
- `from_payload()` używa `.get()` z domyślną wartością dla backward compatibility
- Każda zmiana schematu = inkrementacja `schema_version`

### Repository Port
- Protocol/ABC w `domain/<bc>/repositories/`
- Definiuje kontrakt: `save()`, `get_by_id()`, `list_by_*()`, `delete()`, `exists()`
- Operuje na typach domenowych (agregaty, VO)
- Nie używa `store()`, `persist()`, `add()`, `update()` — tylko `save()`

### Domain Service
- Stateless, bez własnego stanu/tożsamości
- Używany gdy logika operuje na wielu agregatach tego samego BC
- Może używać innych Domain Services
- Porty (Protocol) dla zależności zewnętrznych
- Wstrzykiwany jako singleton przez DI

### Domain Exception
- Dziedziczy po `DomainError` z platformy
- Każdy invariant ma dedykowaną klasę wyjątku
- Nigdy ogólny `ValueError` czy `RuntimeError` dla reguł biznesowych

### Zakazy w warstwie domenowej
- Nie importuje: `sqlalchemy`, `pydantic`, `fastapi`, `motor`
- Nie importuje: `shell.application.*`, `shell.infrastructure.*`, `shell.framework.*`, `shell.bootstrap.*`
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
