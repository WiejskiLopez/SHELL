---
name: shell-architecture
description: Architektura i konwencje projektowe dla repozytorium SHELL (Python, Clean Architecture + DDD + Hexagonal + CQRS, SQLAlchemy async, FastAPI). Używaj zawsze, gdy modyfikujesz, dodajesz lub review'ujesz kod w katalogu `shell/` — dodawanie nowej funkcjonalności, nowe aggregate/entity/VO, handlery command/query/event, mappery, repozytoria SQL/InMemory, migracje Alembic, rejestracja w DI, refaktoryzacja relacji między agregatami. Używaj także przy analizie błędów logicznych, planowaniu refaktoryzacji warstwowej, albo gdy nie jesteś pewien gdzie powinna trafić nowa klasa.
---

# SHELL — Architektura i konwencje

Projekt SHELL to system execution-orkiestracji oparty na **Clean Architecture + DDD + Hexagonal + CQRS**, napisany w Pythonie z SQLAlchemy 2.0 async i FastAPI. Ten skill podpowiada, jak pisać kod zgodny z konwencjami projektu i jak unikać klas błędów, które już tu wystąpiły.

## Architektura warstwowa

Kierunek zależności jest jednokierunkowy:

```
domain/ ← application/ ← infrastructure/ ← framework/ ← bootstrap/
```

- `domain/` — czysty Python, reguły biznesowe (Entity, VO, Aggregate Root, Domain Events, Repository porty)
- `application/` — orkiestracja przypadków użycia (Command/Query/Event Handlers, UoW, DTO, Mapper)
- `infrastructure/` — implementacje portów (SQLAlchemy, InMemory, outbox, migracje)
- `framework/` — FastAPI, CLI, entrypointy
- `bootstrap/` — Composition Root (DI Containery, Factory)

Reguły importów i zakazy (`domain/` nigdy nie importuje `sqlalchemy`/`pydantic`/`fastapi`) — patrz `references/layers-and-dependencies.md`.

## Krytyczne invariants (czytaj najpierw)

To reguły, których złamanie już wielokrotnie wyprodukowało błędy runtime i deadlocki w tym kodzie. Każda ma swój odpowiednik w `references/anti-patterns.md`.

### ⚠️ 0. Primitive Obsession — zero typów prostych w domenie

W warstwie `domain/` NIE WOLNO używać typów prostych (`str`, `int`, `float`, `bool`, `dict`, `list`, `set`, `Any`) jako typów pól w:

- **Agregatach** — każde pole musi być ValueObject, Entity, ID (typ kończący się na `Id`) lub kolekcją VO (`list[SomeVO]`)
- **Encjah** — jw.
- **Eventach domenowych** — każde pole musi być ValueObject (`str`, `dict` są zabronione, nawet `dict[str, object]`)
- **Repozytoriach (porty)** — parametry i zwracane typy muszą być ValueObject lub ID; `str`, `int`, `bool` są zabronione
- **Portach domenowych (Protocol)** — jw.

**Dozwolone wyjątki**: `datetime` (tylko jako znacznik czasu w encji/eventach), typy w `TYPE_CHECKING` blokach, parametry w `from_payload()` (deserializacja).

**Test weryfikujący**: `shell/tests/platform/architecture/test_domain_structure.py`:
- `test_entity_aggregate_fields_have_domain_types` — sprawdza entity/aggregate
- `test_domain_event_fields_have_domain_types` — sprawdza eventy
- `test_repository_port_signatures_have_domain_types` — sprawdza porty repozytoriów

Przykład ZŁY:
```python
class Workflow(AggregateRoot[WorkflowId]):
    _status: str           # ZŁO: str zamiast WorkflowStatus
    _goal: str             # ZŁO: str zamiast Goal
    _skills: list          # ZŁO: bare list bez typu
```

Przykład DOBRY:
```python
class Workflow(AggregateRoot[WorkflowId]):
    _status: WorkflowStatus        # VO
    _created_at: datetime          # stdlib — dozwolony
    _skills: list[WorkflowSkill]   # kolekcja encji
    _state_inputs: list[WorkflowStateInput]  # kolekcja encji
```

Przykład ZŁY w evencie:
```python
@dataclass
class WorkflowFailedEvent(DomainEvent):
    reason: str           # ZŁO: str zamiast Reason
    details: dict         # ZŁO: dict zamiast StateData
```

Przykład DOBRY w evencie:
```python
@dataclass
class WorkflowFailedEvent(DomainEvent):
    reason: Reason              # VO
    details: StateData          # VO
```

### 1. Persistence round-trip — każde pole persystowane dotyka 6 miejsc

Gdy dodajesz/usuwasz pole agregatu, które ma przetrwać restart procesu, dotknij w jednym PR: agregat domeny, SQL model, mapper w obu kierunkach, InMemory repo, mapper DTO, handlery produkcyjne. Pomięcie któregokolwiek = pole tracone przy reloadzie albo `AttributeError` w mapperze. Patrz antywzorzec #1.

### 2. Emisja eventów przejścia stanu — bezwarunkowa

Jeśli metoda domenowa realizuje przejście stanu agregatu (`idle → running`, `running → done`), emituj event bezwarunkowo. Nie uzależniaj emisji od obecności optionala w parametrach — sagi subskrybujące ten event nigdy się nie obudzą i potok utknie. Patrz antywzorzec #2.

### 3. Lookup po unikalnym ID właściciela, nie współdzielonym FK

Jeśli klucz jest współdzielony między kilkoma rekordami (np. sub-graf i parent mają ten sam `task_execution_id`), lookup po nim jest niejednoznaczny — SQL rzuci `MultipleResultsFound`, in-memory zwróci losowy. Szukaj zasobu po ID jego właściciela (np. `get_by_workflow_id`). Patrz antywzorzec #3.

### 4. Model ORM ↔ migracja Alembic zgodne co do kolumny

Każda zmiana modelu ORM wymaga migracji w tym samym PR. Rozjazd objawia się `OperationalError` dopiero w runtime. Patrz antywzorzec #4.

### 5. Adapter symmetry — InMemory = SQL

InMemory repo implementuje pełen kontrakt portu z identyczną semantyką co SQL. No-op stub (`return None`) maskuje błędy w testach jednostkowych — ujawnią się dopiero na SQL. Patrz antywzorzec #6.

### 6. `stage_events(pull_events())` po każdej mutacji w handlerze

W handlerze po mutacji agregatu wołaj `unit_of_work.stage_events(aggregate.pull_events())`. Bez tego eventy domenowe nie trafią do outboxu i sagi ich nie dostaną.

## Kiedy czytać references

- Zaczynasz nową funkcjonalność i nie wiesz gdzie co trafia → `references/checklists.md` (sekcja "Dodawanie nowej funkcjonalności")
- Piszesz nowy aggregate/entity/VO/event/domain service → `references/domain.md`
- Piszesz handler, mapper, strategię, port aplikacyjny → `references/application.md`
- Piszesz handler z zasadami między-domenowymi → `references/application-handlers.md`
- Piszesz repozytorium SQL/InMemory, model ORM, migrację → `references/infrastructure.md`
- Modyfikujesz relacje między agregatami, dodajesz/usuwasz pole, robisz refaktoryzację warstwową → `references/anti-patterns.md` (OBOWIĄZKOWO — to zapobiega ~80% błędów)
- Rejestrujesz nowy handler w DI → `references/checklists.md` (sekcja "Bootstrap wiring")
- Nie jesteś pewien struktury pliku → `references/checklists.md` (sekcja "Cross-cutting")
- Pracujesz z Workflow/GraphExecution/GraphNodeExecution → `references/execution-hierarchy.md` (poziomy, relacje, Mode enum)
- Dodajesz sub-graf, PLANNER, TASKER, extension point → `references/sub-graph-extension-points.md` (przepływy, Protocols, reguły)

## Przepis: nowa funkcjonalność (wersja skrócona)

1. **Domain**: VO / Entity / Aggregate Root / Event / Exception / Service / Repository Port w `domain/`
2. **Application**: Command/Query + Handler + DTO + Mapper w `application/`
3. **Infrastructure**: ORM Model + migracja Alembic + SQL Repository + InMemory Repository w `infrastructure/`
4. **DI**: Container + Factory w `bootstrap/`
5. **Framework**: Router FastAPI albo komenda CLI w `framework/`
6. **Testy**: unit (domain + application) + integration (SQLite) + E2E

Pełna checklist (z numeracją kroków i podkatalogami) w `references/checklists.md`.

## Najczęstsze pułapki (skrót)

Pełna lista 12 antywzorców z realnymi przykładami w `references/anti-patterns.md`. Tu tylko sygnały ostrzegawcze:

- Modyfikujesz relację między agregatami → lockstep 6 miejsc (antywzorzec #1)
- Dodajesz/usuwasz pole → grep po konsumentach, nie zostawiaj hardcoded `""`/`None`/`[]` (antywzorzec #5)
- Zmieniasz typ zwrotny metody `X | None` → `list[X]` → usuń martwe `if x is None` (antywzorzec #8)
- Bierzesz `list[0]` z zapytania → dodaj `order_by` (antywzorzec #9)
- Zapisujesz dwa agregaty w jednej operacji → atomowo albo retry całości (antywzorzec #12)

## Konwencje kodu (w skrócie)

- Każdy plik `.py` (poza `__init__.py`, migracjami, testami) zaczyna się od `from __future__ import annotations`
- Type hints obowiązkowe (mypy strict)
- `__init__.py` tylko re-eksportuje, nigdy nie definiuje klas
- Brak komentarzy w kodzie produkcyjnym, brak emoji

Szczegóły w `references/checklists.md`.
