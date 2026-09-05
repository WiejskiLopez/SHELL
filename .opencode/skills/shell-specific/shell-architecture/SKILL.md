---
name: shell-architecture
description: "Architektura i konwencje projektowe dla repozytorium SHELL (Python, Clean Architecture + DDD + Hexagonal + CQRS, SQLAlchemy async, FastAPI). Używaj zawsze, gdy modyfikujesz, dodajesz lub review'ujesz kod w katalogu `shell/` — dodawanie nowej funkcjonalności, nowe aggregate/entity/VO, handlery command/query/event, mappery, repozytoria SQL/InMemory, migracje Alembic, rejestracja w DI, refaktoryzacja relacji między agregatami. Używaj także przy analizie błędów logicznych, planowaniu refaktoryzacji warstwowej, albo gdy nie jesteś pewien gdzie powinna trafić nowa klasa."
---

# SHELL — Architektura i konwencje

Projekt SHELL to system execution-orkiestracji oparty na **Clean Architecture + DDD + Hexagonal + CQRS**, napisany w Pythonie z SQLAlchemy 2.0 async i FastAPI. Ten skill podpowiada, jak pisać kod zgodny z konwencjami projektu i jak unikać klas błędów, które już tu wystąpiły.

## Docelowa topologia pakietów i testów

For focused work, load the dedicated concept skill instead of relying on this
overview alone:

- `package-topology` — package/file ownership;
- `platform-boundary` — generic platform rules;
- `bounded-context-boundary` — BC isolation and standalone composition roots;
- `test-topology` — ownership and placement of tests;
- `integration-contracts` — HTTP/event communication between BCs.
- `resilient-http-client` — timeout, retry, circuit breaker and authenticated
    HTTP clients for service-to-service calls;
- `provider-service-separation` — rozdzielenie portów odczytu (`Provider`) od
    portów operacji i mutacji (`Service`) między BC.
- `enterprise-over-hacks` — zasada decyzyjna: przy każdym wyborze architekt wybiera
    rozwiązanie enterprise (jawne, deterministyczne, standardowe, czytelne w PR,
    niskie zadłużenie) zamiast skrótu bez udokumentowanej przyczyny.

Kod żyje wyłącznie w `shell/platform/` oraz `shell/<bc>_service/{...}/<bc>/`; wspólne
top-level pakiety `shell/domain`, `shell/application`, `shell/infrastructure`,
`shell/framework`, `shell/process` i `shell/bootstrap` są poza strukturą repo.

- `shell/platform/` zawiera generyczne, współdzielone prymitywy i kontrakty platformy;
    platforma importuje wyłącznie własne moduły (`shell.platform.*`).
- `shell/<bc>_service/{domain,application,process,infrastructure,framework,bootstrap}/<bc>/`
    zawiera kod i composition root wyłącznie konkretnego BC. Warstwa `process/`
    (sagi/process managery) istnieje dziś w `project_service` (pilotażowa
    `ProjectProvisionSaga`); w pozostałych BC jest warstwą docelową.
- Wspólne mechanizmy techniczne implementujesz jednokrotnie w `shell/platform/`;
    wszystkie BC korzystają z tych samych platformowych klas i adapterów (np.
    `InboxEventModel`, `OutboxEventModel`, publisher, processor, relay) bez kopii per BC.
- Platformowa implementacja współistnieje z osobnymi bazami per BC: każdy BC używa
    tych samych klas platformy z własnym `DATABASE_URL`, własną sesją i migracjami;
    tabele o tej samej nazwie żyją w osobnych bazach.
- Każdy bounded context posiada własny composition root i samodzielny lifecycle wdrożenia.
- Komunikacja między BC przebiega przez publiczne kontrakty HTTP lub eventowe.

Testy mają tę samą granicę własności:

- `shell/tests/platform/` — tylko testy `shell.platform` (import BC poza tym katalogiem).
- `shell/tests/<bc>/` — testy jednego BC; dozwolone są własny BC i platforma.
- `shell/tests/contracts/` — publiczne kontrakty HTTP/event między BC.
- `shell/tests/system/` — scenariusze wielu osobnych aplikacji BC.
- `shell/tests/architecture/` — centralne testy AST/importów i reguł całego repozytorium.
- `shell/tests/shared/` — helpery generyczne (importy BC poza tym katalogiem).

Test umieszczony w `platform`, który importuje BC, należy zgeneryzować na fake
platformowy albo przenieść do `shell/tests/<bc>`. Test architektury pozostaje w
`shell/tests/architecture`, nawet jeśli sprawdza regułę dotyczącą platformy.

## Architektura warstwowa

Kierunek zależności jest jednokierunkowy (per pakiet serwisu BC, np. `shell/execution_service/`):

```
shell/<bc>_service/domain/<bc>/ ← application/ ← infrastructure/ ← framework/ ← bootstrap/
```

Warstwa `process/` (sagi/process managery, obecnie `project_service`) jest
**dodatkową warstwą zależną wyłącznie od `domain/` i `application/`** — nie
importuje `infrastructure/`/`framework/`/`bootstrap/` (egzekwuje
`test_imports__test_process_layer_imports.py`). Mechanizm sagi żyje w bibliotece
`saga-orchestration` (`packaging/saga-orchestration`).

- `shell/<bc>_service/domain/<bc>/` — czysty Python i reguły biznesowe BC.
- `shell/<bc>_service/application/<bc>/` — atomowe handlery przypadków użycia BC.
- `shell/<bc>_service/process/<bc>/` — orkiestracja i sagi BC (warstwa docelowa; zrealizowana w `project_service`).
- `shell/<bc>_service/infrastructure/<bc>/` — implementacje portów i adaptery BC.
- `shell/<bc>_service/framework/<bc>/` — FastAPI, CLI i entrypointy BC.
- `shell/<bc>_service/bootstrap/<bc>/` — composition root wyłącznie tego BC.

Reguły importów per warstwa (np. `domain/` importuje wyłącznie stdlib i własne typy;
sterling stack techniczny używa się w warstwach wyżej) — patrz `references/layers-and-dependencies.md`.

## Struktura katalogów — rodzeństwo i liczba mnoga

Katalog pojęcia i katalog jego handlerów są **rodzeństwem na tym samym poziomie**,
zawsze w **liczbie mnogiej**:

```
commands/          +  command_handlers/
queries/           +  query_handlers/
events/            +  event_handlers/
integration_events/ + event_handlers/
```

- **Zakaz zagnieżdżania**: NIGDY `command/handlers/` ani `event/handlers/` — handlery idą obok pojęcia, nie pod spodem.
- **Zakaz liczby pojedynczej**: `command/`, `command_handler/`, `event/`, `event_handler/` — używaj mnogiej.
- Obowiązuje dla `commands/`/`queries/` w każdym BC (`shell/<bc>_service/application/<bc>/<aggregate>/`) oraz w platformie (`shell/platform/application/`). Pary `events/`+`event_handlers/` i `integration_events/`+`event_handlers/` są regułą docelową — dziś `event_handlers/` istnieją w platformie i `session_service`, pozostałe BC mają `integration_events/` bez rodzeństwa handlerów.

Pełne reguły i przykłady: `naming-standards/directory-naming-standards` (sekcja "Zasada rodzeństwa (siblings)").

## Krytyczne invariants (czytaj najpierw)

To reguły, których złamanie już wielokrotnie wyprodukowało błędy runtime i deadlocki w tym kodzie. Każda ma swój odpowiednik w `references/anti-patterns.md`.

### ⚠️ 0. Primitive Obsession — zero typów prostych w domenie

W warstwie `domain/` NIE WOLNO używać typów prostych (`str`, `int`, `float`, `bool`, `dict`, `list`, `set`, `Any`) jako typów pól w:

- **Agregatach** — każde pole musi być ValueObject, Entity, ID (typ kończący się na `Id`) lub kolekcją VO (`list[SomeVO]`)
- **Encjah** — jw.
- **Eventach domenowych** — każde pole musi być ValueObject (`str`, `dict` są zabronione, nawet `dict[str, object]`)
- **Repozytoriach (porty)** — parametry i zwracane typy muszą być ValueObject lub ID; `str`, `int`, `bool` są zabronione
- **Portach domenowych (Protocol)** — jw.

**Dozwolone wyjątki**: `datetime` (tylko jako znacznik czasu w encji/eventach), typy w `TYPE_CHECKING` blokach, parametry w `PayloadObjectDeserializer` (deserializacja).

**Test weryfikujący**: `shell/tests/architecture/test_domain_structure__*.py`:
- `test_entity_aggregate_fields_have_domain_types` — sprawdza entity/aggregate
- `test_domain_event_fields_have_domain_types` — sprawdza eventy
- `test_repository_port_signatures_have_domain_types` — sprawdza porty repozytoriów

Przykład ZŁY:
```python
class Workflow(AggregateRoot[WorkflowId]):
    _status: str           # Antywzorzec: str zamiast WorkflowStatus
    _goal: str             # Antywzorzec: str zamiast Goal
    _skills: list          # Antywzorzec: bare list bez typu
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
    reason: str           # Antywzorzec: str zamiast Reason
    details: dict         # Antywzorzec: dict zamiast StateData
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
- Piszesz Query Service → port w `shell/<bc>_service/application/<bc>/<aggregate>/ports/<aggregate>_query_service.py` (patrz [query-handler-structure](../../pattern-standards/query-handler-structure/SKILL.md#query-service--lokalizacja-per-agregat))
- Piszesz handler z zasadami między-domenowymi → `references/application-handlers.md`
- Piszesz repozytorium SQL/InMemory, model ORM, migrację → `references/infrastructure.md`
- Implementujesz adapter danych międzyagregatowych → wzorce Aggregate Provider (odczyt) i Command Port (operacje); porty w `ports/`, adaptery w `infrastructure/<bc>/<aggregate>/adapters/<nazwa>/`
- Projektujesz integrację tylko do odczytu albo operację na innym BC → `provider-service-separation` (Provider vs Service, lokalne mapowanie kontraktów i własność portu)
- Piszesz Event Handler → `shell/<bc>_service/application/<bc>/<aggregate>/event_handlers/` (patrz [event-handler-structure](../../pattern-standards/event-handler-structure/SKILL.md))
- Modyfikujesz relacje między agregatami, dodajesz/usuwasz pole, robisz refaktoryzację warstwową → `references/anti-patterns.md` (OBOWIĄZKOWO — to zapobiega ~80% błędów)
- Rejestrujesz nowy handler w DI → `references/checklists.md` (sekcja "Bootstrap wiring")
- Nie jesteś pewien struktury pliku → `references/checklists.md` (sekcja "Cross-cutting")
- Pracujesz z Workflow/GraphExecution/NodeExecution → `references/execution-hierarchy.md` (poziomy, relacje, Mode enum)
- Dodajesz sub-graf, PLANNER, TASKER, extension point → `references/sub-graph-extension-points.md` (przepływy, Protocols, reguły)

## Przepis: nowa funkcjonalność (wersja skrócona)

1. **Domain**: VO / Entity / Aggregate Root / Event / Exception / Service / Repository Port w `domain/`
2. **Application**: Atomowy Command/Query + Handler + DTO + Mapper w `application/`; Query Services w `query_services/<nazwa_agregatu>/`
3. **Process** (jeśli potrzeba orkiestracji): Saga/Process Manager + handlers + commands + ports w `process/`
4. **Infrastructure**: ORM Model + migracja Alembic + SQL Repository + InMemory Repository + adaptery portów międzyagregatowych (wzorce Aggregate Provider / Command Port)
5. **DI**: Container + Factory w `bootstrap/`
6. **Framework**: Router FastAPI albo komenda CLI w `framework/`
7. **Testy**: unit (domain + application + process) + integration (SQLite) + E2E

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
