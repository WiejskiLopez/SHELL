# Agent — Reguły Architektoniczne projektu SHELL

## 1. Architektura warstwowa (Clean Architecture + DDD + Hexagonal + CQRS)

```
domain/ ← application/ ← infrastructure/ ← framework/ ← bootstrap/
```

### Reguły zależności (egzekwowane przez `tests/architecture/test_imports.py` i `import-linter`)

| Warstwa | Może importować | Przykładowa zawartość |
|---------|----------------|----------------------|
| `domain/` | Tylko stdlib | Entities, Value Objects, Aggregate Roots, Domain Events, Repository porty (Protocol), Domain Services, Domain Exceptions, Domain Ports |
| `application/` | `domain/` + stdlib | Command/Query/Event Handlers, CommandBus/QueryBus/EventBus, DTO, Mapper, Strategy, Application Ports (Protocol) |
| `infrastructure/` | `domain/` + `application/` + biblioteki zewn. | SQLAlchemy ORM modele, SQL Reposytoria, InMemory adapters, logging, messaging (outbox/inbox), serializacja, system clock |
| `framework/` | Wszystkie niższe warstwy | FastAPI app + routers + middleware, CLI (argparse), entrypointy, orchestration runner |
| `bootstrap/` | Wszystkie warstwy (Composition Root) | DI Containery, Factory klasy, konfiguracja, setup logowania — to jedyne miejsce gdzie tworzone są konkretne implementacje |
| `shared/` | Tylko stdlib | Narzędzia cross-cutting (UUID generator, serializacja) |

### Kluczowe zakazy
- `domain/` NIGDY nie importuje: `sqlalchemy`, `pydantic`, `fastapi`, `motor`, `shell.application`, `shell.infrastructure`, `shell.framework`, `shell.bootstrap`
- `application/` NIGDY nie importuje: `sqlalchemy`, `fastapi`, `motor`, `shell.infrastructure`, `shell.framework`, `shell.bootstrap`
- Żadna warstwa nie ma bezpośredniej wiedzy o innych warstwach poza dozwolonym kierunkiem zależności
- Wszystkie zależności między warstwami idą przez porty (Protocol) — NIGDY przez konkretne implementacje

---

## 2. Domain Layer — reguły

### Entity
- **OBOWIĄZKOWO** dziedziczy po `Entity[TId]` z `domain/entities/base/entity.py`
- Tożsamość oparta na `id` — `__eq__` i `__hash__` tylko po identyfikatorze
- Stan mutowalny, ale identyfikator (`_id`) niemutowalny po konstrukcji — prywatny atrybut, publiczny property `id`
- Używaj `__slots__` dla oszczędności pamięci (NIGDY nie powtarzaj `_id` w slots — jest dziedziczony)
- Każde Entity ma dedykowany Value Object jako ID (np. `TaskExecutionId`)
- NIGDY nie używaj `@dataclass` dla Entity — stracisz identity-based equality

### Child Entity (encja wewnątrz agregatu bez własnej tożsamości globalnej)
- Nie dziedziczy po `Entity[TId]` — nie ma własnej tożsamości poza agregatem
- Może być `@dataclass(slots=True)` jeśli nie potrzebuje identity-based `__eq__`/`__hash__`
- Zawsze istnieje tylko w kontekście swojego Aggregate Root
- Przykład: `Message` (istnieje tylko w `Session`), `RagChunk` (istnieje tylko w `RagDocument`)

### Aggregate Root
- **OBOWIĄZKOWO** dziedziczy po `AggregateRoot[TId]` z `domain/entities/base/aggregate_root.py`
- Prywatny bufor zdarzeń: `append_event()` i `pull_events()`
- Aggregate Root jest granicą transakcji — cały zapis w ramach jednego AR to jedna transakcja
- Tylko Aggregate Root emituje zdarzenia domenowe
- Każda metoda modyfikująca stan agregatu musi wołać `append_event()` z odpowiednim DomainEvent

### Value Object
- Immutable: `@dataclass(frozen=True, slots=True)`
- Walidacja w `__post_init__`
- Obowiązkowa metoda `__str__`
- Brak tożsamości — dwa VO z tymi samymi wartościami są wymienne
- Typy ID: każdy jako osobna klasa z kompletem: `@dataclass(frozen=True, slots=True)`, `__post_init__` (walidacja non-empty), `__str__`, `@classmethod generate()`

### Domain Event
- Niezmienne dataclasses w `domain/events/events/`
- Każdy event w osobnym pliku
- Nazewnictwo: przeszłość dokonana (np. `TaskExecutionCreated`, `WorkflowCompleted`, `EnvelopeRouted`)
- Eventy są faktami — zawierają tylko dane które się wydarzyły, nie instrukcje

### Domain Service
- W `domain/services/` — operacje które nie pasują do żadnej encji lub VO
- Są bezstanowe (stateless)
- Pracują wyłącznie na obiektach domenowych
- Przykłady: `EnvelopeLifecycleService`, `GraphNodeExecutionNavigator`, `GraphNodeExecutionPolicy`

### Domain Exception
- W `domain/exceptions/` — osobna klasa dla każdego przypadku
- Dziedziczą po bazowej `DomainError` z `_base.py`
- Niosą kontekst domenowy (np. ID encji, nieprawidłową wartość)

### Repository Port (Domain)
- Interface (Protocol) w `domain/repositories/`
- Operacje nazywane językiem domeny: `save()`, `get_by_id()`, `next_version()`, `find_latest_by_*()`
- NIGDY nie ujawniają persystencyjnych detali (SQL, ORM, kolekcje)
- Metody zwracają/w przyjmują wyłącznie obiekty domenowe

---

## 3. Application Layer — reguły

### CQRS — Command / Query Separation
- **Commands**: zmieniają stan, zwracają `None` lub ID utworzonego obiektu
- **Queries**: nie zmieniają stanu, zwracają DTO
- Każda komenda/kwerenda w osobnej klasie w `application/commands/` lub `application/queries/`
- Każdy handler w osobnej klasie w `application/command_handlers/` lub `application/query_handlers/`
- Handler spełnia kontrakt Callable: `handle(command: TCommand) -> Any`

### Command / Query Bus
- `CommandBus` → rejestracja command_type → handler_factory
- `QueryBus` → rejestracja query_type → handler_factory
- Bus jest tylko dispatcherem — nie zawiera logiki biznesowej
- Busy są konfigurowane w `bootstrap/`

### Application Port (Protocol)
- W `application/ports/` — interfejsy dla adapterów infrastrukturalnych
- Każdy w osobnym module (np. `unit_of_work.py`, `time.py`, `logging.py`)
- Obowiązkowe porty: `UnitOfWork`, `Clock`, `IdGenerator`, `EventPublisher`, `Logger`, `NodeProcessRunner`, `NodeWorkspace`, `TaskExecutionLoader`
- `ports.py` agreguje re-exporty dla wygody

### DTO (Data Transfer Object)
- W `application/dto/` — proste dataclasses lub Pydantic modele
- Służą wyłącznie do przenoszenia danych między warstwami
- NIGDY nie zawierają logiki biznesowej

### Mapper
- W `application/mappers/` — konwersja Entity ↔ DTO
- Statyczne metody lub osobne klasy
- Mapper jest własnością warstwy aplikacyjnej

### Strategy — NodeExecutionStrategy
- W `application/strategies/graph_node_execution_strategy/`
- `protocol.py` definiuje kontrakt (Protocol) z adnotacją `@runtime_checkable`
- `_base_strategy.py` — wspólna logika dla wszystkich strategii (budowa Manifest + runner.run)
- Klasy strategii różnią się tylko wartością `mode`: `AgentStrategy`, `RouterStrategy`, `TaskerStrategy`, `ToolStrategy`, `WorkerStrategy`
- Strategie są singletonami w rejestrze — NIE dodawaj stanu mutowalnego do strategii
- `registry.py` — rejestr dostępnych strategii z rzucaniem `InvalidNodeMode` dla nieznanych trybów
- Nowy tryb = nowa klasa `*Strategy(mode="nazwa")` + rejestracja w `registry.py`

### Handler — struktura

#### Single-phase UoW (dla krótkich operacji synchronicznych)
```python
class SomeHandler:
    def __init__(self, uow: UnitOfWork, logger: Logger, ...) -> None: ...
    async def handle(self, command: SomeCommand) -> None:
        async with self._uow as uow:
            aggregate = await uow.some_repo.get_by_id(command.some_id)
            aggregate.do_something()          # ← append_event() wewnątrz
            uow.stage_events(aggregate.pull_events())  # ← OBOWIĄZKOWE
        # commit() przez __aexit__
```

#### Two-phase UoW (dla długotrwałych operacji np. subprocess)
Gdy między pobraniem agregatu a zapisem wyniku jest długotrwała operacja zewnętrzna
(np. `NodeProcessRunner.run()`), NIE trzymaj otwartej transakcji na ten czas.
Użyj dwóch osobnych bloków UoW:

```python
async def handle(self, command: SomeCommand) -> None:
    # Phase 1: załaduj i oznacz stan przed operacją zewnętrzną
    async with self._uow as uow:
        workflow = await uow.workflows.get_by_id(command.workflow_id)
        workflow.mark_running()
        uow.stage_events(workflow.pull_events())
    # ← transakcja zapisana, sesja zwolniona

    # Długotrwała operacja zewnętrzna (bez otwartej transakcji)
    result = await self._runner.run(...)

    # Phase 2: zapisz wynik po operacji zewnętrznej
    async with self._uow as uow:
        workflow = await uow.workflows.get_by_id(command.workflow_id)
        workflow.record_result(result)
        uow.stage_events(workflow.pull_events())
```

Zasady two-phase UoW:
- **Phase 1**: tylko załaduj + ustaw status "w trakcie" + commit
- **Operacja zewnętrzna**: bez otwartej transakcji — nie blokuj bazy
- **Phase 2**: załaduj ponownie (wersja mogła się zmienić) + zapisz wynik + commit
- Oba bloki muszą wołać `stage_events()`

#### Handler completeness checklist
Każdy handler (command/event) musi przejść tę checklistę:

1. `from __future__ import annotations` — obecny na górze pliku
2. `TYPE_CHECKING` — importy domenowe pod guardem jeśli nie są używane w runtime
3. `async with self._uow as uow:` — UoW jako async context manager
4. Pobranie agregatu przez `uow.<repo>.get_by_id()`
5. Mutacja agregatu przez metody domenowe (które wołają `append_event()`)
6. **`uow.stage_events(aggregate.pull_events())`** — OBOWIĄZKOWE po każdej mutacji
7. Commit przez `__aexit__` — NIGDY ręcznego `uow.commit()`
8. Typowanie: sygnatura `handle` z `-> None` dla command, `-> list[Dto]` dla query

---

## 4. Infrastructure Layer — reguły

### Port-to-Adapter inheritance (obowiązkowe)
Każdy adapter infrastrukturalny (SQL + InMemory) MUSI jawnie implementować port domenowy:

```python
# DOMAIN PORT
class WorkflowRepository(Protocol):
    async def get_by_id(self, id: WorkflowId) -> Workflow | None: ...

# SQL ADAPTER — jawna implementacja
class SqlWorkflowRepository(WorkflowRepository):
    ...

# INMEMORY ADAPTER — jawna implementacja  
class InMemoryWorkflowRepository(WorkflowRepository):
    ...
```

Zapewnia to:
- Symetrię między SQL i InMemory — oba implementują ten sam kontrakt
- Type-checking — mypy wychwyci brakującą metodę w adapterze
- Runtime safety — `isinstance` działa poprawnie (jeśli Protocol jest `@runtime_checkable`)

### SQL Repositories
- Implementują porty z `domain/repositories/` przez jawne dziedziczenie
- W `infrastructure/persistence/sql/repositories/`
- Używają SQLAlchemy 2.0 async ORM
- Dialekt wybierany runtime'm przez `database_url` — jeden zestaw modeli i repozytoriów dla SQLite i PostgreSQL
- Mapowanie ORM → Domain: w `infrastructure/persistence/sql/mappers/` (nie w repozytorium)
- NIGDY nie importują domain entity w runtime — zawsze pod `TYPE_CHECKING` + mapper
- Każda operacja w kontekście `UnitOfWork` — NIGDY samodzielnego zarządzania sesją
- Konwencja nazewnictwa metod: `get_by_id()`, `save()`, `delete()`, `list_by_*()`, `get_latest_by_*()`

### InMemory Repositories
- W `infrastructure/persistence/memory/`
- Używane wyłącznie w testach jednostkowych
- Implementują te same porty co SQL odpowiedniki przez jawne dziedziczenie
- Przechowują dane w słownikach w pamięci
- NIGDY nie dodają metod których nie ma w porcie domenowym

### ORM Models (SQLAlchemy)
- W `infrastructure/persistence/sql/models/`
- Anemiczne — wyłącznie mapa tabel, NIGDY logiki biznesowej
- Oddzielny model dla każdego agregatu/encji
- Relacje tam gdzie potrzebne, ale bez kaskadowego ładowania przez `selectin`
- Kolumny JSON dla elastycznych struktur

### Outbox / Messaging
- Wzór Transactional Outbox: zapis eventu w tej samej transakcji co domena
- `outbox_event` tabela → `OutboxRelay` → EventPublisher
- Gwarancja at-least-once delivery
- Kompozytowy EventPublisher składa wiele publisherów (log, SQL, audit)

### Migracje (Alembic)
- W `infrastructure/persistence/migrations/sql/versions/`
- Downgrade zawsze obsłużone
- Dialekt-specific DDL przez `op.get_context().dialect.name`

---

## 5. Framework Layer — reguły

### FastAPI
- App factory w `framework/api/app.py`
- Routery w `framework/api/routers/` — cienkie, delegują do handlerów przez bus
- Middleware: correlation_id, error_handler
- Endpointy mapują HTTP → Command/Query → DTO → JSON

### CLI
- Argparse w `framework/cli/` — dispatcher + parser + komendy
- Entrypointy w `framework/entrypoints/` — 5 trybów (agent, router, tasker, tool, worker)

### Środowisko wykonawcze
- Obowiązkowa propagacja `CorrelationId` przez `contextvars`
- Każda operacja (command/event/query) w kontekście CorrelationId

---

## 6. Bootstrap / Composition Root — reguły

- Jedno miejsce gdzie tworzone są wszystkie konkretne implementacje
- `dependency-injector` jako DI framework
- Kontenery w `bootstrap/container/`
- Fabryki w `bootstrap/factory/`
- Konfiguracja przez zmienne środowiskowe (pydantic-settings) — NIGDY hardcoded

### Struktura kontenerów
```
CoreContainer
├── InfrastructureContainer (SQLAlchemy engine, repos, outbox, clock)
├── DomainContainer (domain services)
├── ApplicationContainer
│   ├── BusContainer (command, query, event bus)
│   ├── CommandContainer (rejestracja handlerów)
│   ├── QueryContainer (rejestracja handlerów)
│   └── EventContainer (rejestracja handlerów)
└── MessagingContainer (outbox relay, event publishers)
```

### Bootstrap wiring checklist
Przy dodawaniu nowego handlera (command/query/event) należy przejść checklistę:

1. **Container**: dodaj `providers.Factory(NewHandler, ...)` w odpowiednim kontenerze
   - Command → `command_container.py`
   - Query → `query_container.py`
   - Event → `event_container.py`
2. **Factory**: zarejestruj handler w odpowiedniej funkcji factory
   - `command_factory.py` → `cmd_bus.register(NewCommand, app_ctx.commands.new_handler_factory)`
   - `query_factory.py` → `q_bus.register(NewQuery, app_ctx.queries.new_handler_factory)`
   - `event_factory.py` → `event_bus.subscribe(NewEvent, app_ctx.events.new_handler_factory)`
3. **Weryfikacja**: po rejestracji sprawdź czy:
   - Typ komendy/eventu jest unikalny (CommandBus: 1:1, EventBus: 1:N)
   - Kontener ma wszystkie zależności (infra, domain, buses) podpięte
   - `core_container.py` przekazuje wszystkie wymagane zależności do sub-kontenerów

---

## 7. Zasady Transakcyjne (Unit of Work)

- `UnitOfWork` jest zawsze async context managerem
- Wzorzec: `async with self._uow as uow: ...` w handlerze
- **OBOWIĄZKOWO**: po każdej mutacji agregatu wołaj `uow.stage_events(aggregate.pull_events())`
- `commit()` na `__aexit__` jeśli brak wyjątku
- `rollback()` na `__aexit__` jeśli wyjątek
- Outbox zapisywany w tej samej transakcji co zmiany domenowe
- Dla długotrwałych operacji: **Two-phase UoW** — patrz sekcja Handler

---

## 8. Zdarzenia — Event Flow

```
AggregateRoot.append_event()
    → handler wywołuje UoW.stage_events(aggregate.pull_events())
        → UoW.commit():
            1. Zapis stanu aggregate w SQL
            2. Zapis eventów do outbox_event
            3. Commit transakcji SQL
                → OutboxRelay odczytuje outbox_event
                    → EventPublisher publikuje do kolejki/logów
```

---

## 9. Obsługa błędów — Error Handling

- Domain exceptions → HTTP 4xx w middleware (framework layer)
- Infrastructure exceptions → opakowane w domain exceptions przed przekazaniem wyżej
- Nieobsłużone wyjątki → 500 + log + CorrelationId
- Transactional Outbox gwarantuje, że eventy nie zostaną opublikowane jeśli commit się nie powiedzie
- Idempotencja handlerów: wielokrotne wykonanie tego samego eventu/komendy nie zmienia stanu

---

## 10. Testy — strategia

| Kategoria | Lokalizacja | Co testuje | Adaptery |
|-----------|-------------|------------|----------|
| **Unit (domain)** | `tests/unit/domain/` | Entity, VO, Domain Service, state machine, events | Czyste obiekty domenowe |
| **Unit (application)** | `tests/unit/application/` | Handlery, bus, strategie | `InMemory*` repositories, `Fake*` porty |
| **Integration** | `tests/integration/sql_sqlite/` | SQL Reposytoria, UoW, outbox | SQLite (prawdziwa baza) |
| **Integration** | `tests/integration/sql_postgres/` | PostgreSQL-specific | PostgreSQL przez `PG_TEST_URL` |
| **E2E** | `tests/e2e/api/` | FastAPI endpointy | httpx + prawdziwy DI container |
| **E2E** | `tests/e2e/cli/` | CLI komendy | argparse + prawdziwy DI container |
| **Architecture** | `tests/architecture/test_imports.py` | Zależności importowe | AST parser (nie importuje kodu) |

### Reguły testowe
- Testy jednostkowe NIGDY nie używają bazy danych, frameworka, sieci
- Testy jednostkowe NIE używają `pytest-asyncio` jeśli testowana funkcja jest synchroniczna
- Testy integracyjne i E2E używają `pytest-asyncio` (`asyncio_mode = auto`)
- `InMemory*` adaptery w `infrastructure/persistence/memory/` służą do testów — NIGDY na produkcji
- W testach integracyjnych: czysta baza na każdą funkcję testową (fixturą)

---

## 11. Nazewnictwo i konwencje

| Element | Konwencja | Przykład |
|---------|-----------|----------|
| Pliki z jedną klasą | snake_case | `task_execution_id.py` |
| Katalogi | snake_case | `value_objects/`, `command_handlers/` |
| Klasy | PascalCase | `TaskExecutionId`, `WorkflowStarted` |
| Metody/funkcje | snake_case | `pull_events()`, `get_by_id()` |
| Command/Query | PascalCase + suffix | `StartWorkflowCommand`, `GetWorkflowQuery` |
| Handler | PascalCase + "Handler" | `StartWorkflowHandler`, `GetWorkflowHandler` |
| DTO | PascalCase + "Dto" | `WorkflowDto`, `TaskExecutionListItemDto` |
| Domain Event | Past tense PascalCase | `TaskExecutionCreated`, `WorkflowCompleted` |
| Exception | PascalCase + domain context | `WorkflowNotFoundException`, `InvalidEnvelopeTransitionError` |
| Port/Protocol | PascalCase | `UnitOfWork`, `IdGenerator`, `Clock` |
| Strategy | PascalCase + "Strategy" | `AgentStrategy`, `RouterStrategy` |
| Fixture/test resource | snake_case | `task_execution`, `workflow_repo` |
| Zmienna ID | suffix `_id` | `workflow_id`, `task_execution_id` |

---

## 12. `from __future__ import annotations`

Każdy plik `.py` w kodzie źródłowym (`domain/`, `application/`, `infrastructure/`, `framework/`, `bootstrap/`, `shared/`) zaczyna się od `from __future__ import annotations`.
To pozwala na:
- Odroczoną ewaluację typów (PEP 563 / PEP 649)
- Używanie typów w stringach w TYPE_CHECKING blokach
- Unikanie circular imports przez `TYPE_CHECKING` guardy

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.entities import SomeEntity  # tylko type checking, nie runtime
```

**WYJĄTKI** (nie wymagają `from __future__ import annotations`):
- `__init__.py` puste lub zawierające tylko `__all__`
- Pliki migracji Alembic (`versions/*.py`)
- Pliki testowe (`tests/`)

---

## 13. Zasady cross-cutting

- **Brak komentarzy w kodzie produkcyjnym** — kod jest samodokumentujący się przez nazwy klas/metod/zmiennych
- **Brak emoji w kodzie** — komunikacja w commitach i dokumentacji bez emoji
- **Type hints obowiązkowe** dla wszystkich funkcji/metod (weryfikowane przez mypy)
- **`__all__` w `__init__.py`** — jawny eksport publicznego API każdego modułu
- **Importy w kolejności** (z pustą linią między grupami):
  1. `from __future__ import annotations`
  2. stdlib (`typing`, `dataclasses`, `uuid`, itd.)
  3. pusta linia
  4. zależności zewnętrzne (`sqlalchemy`, `pydantic`, itd.)
  5. pusta linia
  6. wewnętrzne moduły (`shell.domain.*`, `shell.application.*`, itd.)
- **Linter**: ruff (konfiguracja w `shell/pyproject.toml`)
- **Type checker**: mypy (strict mode, konfiguracja w `shell/pyproject.toml`)

---

## 14. Dodawanie nowej funkcjonalności — przepis krok po kroku

1. **Zdefiniuj model domenowy** (jeśli potrzeba):
   - Value Object w `domain/value_objects/`
   - Entity/Aggregate Root w `domain/entities/` lub `domain/aggregates/`
   - Domain Event w `domain/events/events/`
   - Domain Exception w `domain/exceptions/`
   - Domain Service w `domain/services/`
   - Repository Port w `domain/repositories/`

2. **Zdefiniuj operację aplikacyjną**:
   - Command lub Query w `application/commands/` lub `application/queries/`
   - Handler w `application/command_handlers/` lub `application/query_handlers/`
   - Event Handler w `application/event_handlers/`
   - DTO w `application/dto/`
   - Mapper w `application/mappers/`

3. **Zaimplementuj adapter infrastrukturalny**:
   - ORM Model w `infrastructure/persistence/sql/models/`
   - Migracja Alembic w `infrastructure/persistence/migrations/sql/versions/`
   - Repository w `infrastructure/persistence/sql/repositories/`

4. **Zarejestruj w DI**:
   - Container w `bootstrap/container/`
   - Factory w `bootstrap/factory/`

5. **Dodaj endpoint frameworkowy**:
   - Router FastAPI w `framework/api/routers/`
   - Lub komendę CLI w `framework/cli/commands/`

6. **Dodaj testy**:
   - Unit domain w `tests/unit/domain/`
   - Unit application w `tests/unit/application/`
   - Integration w `tests/integration/sql_sqlite/`
   - E2E w `tests/e2e/api/` lub `tests/e2e/cli/`

---

## 15. Entity state — prywatne atrybuty z publicznymi property

Każdy stan mutowalny encji (poza `_id` który jest już prywatny w `Entity[TId]`) MUSI być:
- Prywatny — atrybut z prefiksem `_`
- Eksponowany przez publiczne `@property` (tylko do odczytu)
- Modyfikowany przez metody domenowe, NIGDY przez bezpośrednie przypisanie z zewnątrz


```python
# POPRAWNIE — wzorzec z TaskExecution
class TaskExecution(AggregateRoot[TaskExecutionId]):
    __slots__ = ("_name", "_version", "_hash", "_body", ...)

    @property
    def name(self) -> TaskExecutionName:
        return self._name

    def rename(self, new_name: TaskExecutionName) -> None:
        self._name = new_name

# ŹLE — publiczne atrybuty
# class RunnerConfig(Entity[RunnerConfigId]):
#     __slots__ = ("package_name", "kind", ...)  # ← brak _
#     self.package_name = package_name           # ← publiczny
```

---

## 16. `__init__.py` — tylko re-eksport, nie definicja klas

Plik `__init__.py` w pakiecie NIGDY nie zawiera definicji klas, funkcji ani stałych (poza `__all__`). Służy WYŁĄCZNIE do re-eksportowania publicznego API z podmodułów.

```python
# POPRAWNIE — re-eksport
from .sql_alchemy_uow import SqlAlchemyUnitOfWork
__all__ = ["SqlAlchemyUnitOfWork"]

# ŹLE — definicja klasy w __init__.py
# class SqlAlchemyUnitOfWork: ...  # ← przenieś do osobnego pliku
```

**WYJĄTKI**:
- Puste `__init__.py` (pakiet jako namespace)
- `__init__.py` zawierające tylko `__all__` z importami
- Pliki konfiguracyjne frameworków (np. Alembic `env.py`)

---

## 17. `TYPE_CHECKING` — zakaz dla class base i `isinstance`

Typy używane w:
- Class base list: `class Foo(Entity[SomeId])`
- `isinstance()` check: `isinstance(x, SomeId)`
- `@dataclass` field type z `__post_init__` używającym tego typu

MUSZĄ być importowane w runtime (NIE pod `TYPE_CHECKING`). `from __future__ import annotations` deferuje tylko adnotacje, NIE class base expression ani isinstance.

```python
from __future__ import annotations
from shell.domain.value_objects.ids import SomeId  # ← runtime, bo używane w class base

if TYPE_CHECKING:
    # Tu idą tylko typy używane wyłącznie w adnotacjach
    from shell.domain.other import SomeOther
```

---

## 18. Child entity — tworzona TYLKO przez Aggregate Root

Child entity (np. `Message`, `RagChunk`) są tworzone WYŁĄCZNIE przez metody swojego Aggregate Root. Repozytoria SQL/InMemory oraz mappery mogą wywoływać konstruktor child entity TYLKO do deserializacji z persystencji — NIGDY jako część logiki biznesowej.

```python
# POPRAWNIE — przez metodę AR
class Session(Entity[SessionId]):
    def append_message(self, ...) -> Message:
        msg = Message(id=msg_id, ...)  # ← tworzenie wewnątrz AR
        self.messages.append(msg)
        return msg

# POPRAWNIE — konstruktor w mapperze (deserializacja)
def message_model_to_entity(model):
    return Message(id=MessageId(model.id), ...)  # ← OK: czysta deserializacja

# ŹLE — tworzenie child entity w repozytorium jako logika biznesowa
# class SomeService:
#     def do_stuff(self):
#         msg = Message(id=..., ...)  # ← NIE: logika biznesowa poza AR
```

---

## 19. ADR — Architecture Decision Records

Wszystkie znaczące decyzje architektoniczne dokumentowane są jako ADR w `shell/docs/adr/`.
Obowiązujące ADR-y:
- **ADR-0001**: Single bounded context — wszystkie tryby w jednym kontekście
- **ADR-0002**: Strategy pattern — tryby egzekucji jako strategie, nie moduły
- **ADR-0003**: Wspólny SQL adapter — jeden zestaw modeli dla SQLite i PostgreSQL
- **ADR-0004**: Step-by-step node execution — wykonanie węzła krok po kroku

---
