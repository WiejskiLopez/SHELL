---
name: di-composition-root
description: Zasady projektowania Composition Root / Dependency Injection w architekturze hexagonalnej — struktura modułów DI per BC, lifecycle (singleton/transient/scoped), rejestracja port-adapter, factory dla handlerów, testowanie z kontenerem. Używaj gdy konfigurujesz DI dla nowego BC, dodajesz nową rejestrację, albo refaktoryzujesz bootstrap.
---

# DI / Composition Root w Enterprise DDD

## 1. Composition Root — Jedno Miejsce

**Composition Root** to jedyne miejsce w aplikacji, gdzie tworzone są zależności. Znajduje się w `shell/bootstrap/`.

```
shell/bootstrap/
├── main.py                       # Główny composition root / CLI entrypoint
├── platform/                     # DI dla platformy (cross-cutting)
│   ├── container/
│   │   ├── core_container.py
│   │   ├── domain_container.py
│   │   ├── application_container.py
│   │   ├── command_container.py
│   │   ├── query_container.py
│   │   ├── event_container.py
│   │   ├── infrastructure_container.py
│   │   └── bus_container.py
│   ├── config/
│   └── factory/
│       ├── command_factory.py
│       ├── query_factory.py
│       └── event_factory.py
├── definition/                   # DI per BC
│   └── container/
├── execution/
│   ├── container/
│   │   └── execution_core_container.py
│   └── factory/
│       └── application_factory.py
├── session/
│   └── container/
└── user/
    └── container/
```

## 2. Moduły DI Per Bounded Context

Każdy BC ma własny moduł DI, który rejestruje wszystkie zależności danego kontekstu. Moduły są niezależne.

```python
# shell/bootstrap/execution/container/execution_core_container.py
from dependency_injector import containers, providers

from shell.domain.execution.repositories.execution_repository import ExecutionRepository
from shell.domain.execution.services.execution_creation_service import ExecutionCreationService
from shell.infrastructure.execution.repositories.sql_execution_repository import SqlExecutionRepository
from shell.infrastructure.execution.mappers.execution_mapper import ExecutionMapper


class ExecutionContainer(containers.DeclarativeContainer):
    """Kontener DI dla Execution Bounded Context."""

    # Port → Adapter
    execution_repository = providers.Factory(
        SqlExecutionRepository,
    )

    # Domain Services (singleton — stateless)
    execution_creation_service = providers.Singleton(
        ExecutionCreationService,
    )

    # Mapper (transient — nowa instancja za każdym razem)
    execution_mapper = providers.Factory(
        ExecutionMapper,
    )
```

## 3. Rejestracja Port → Adapter

Każdy port (Protocol/ABC) jest rejestrowany z konkretną implementacją. Dzięki temu kod domenowy nie wie o istnieniu adapterów.

```python
# Rejestracja Port → Adapter w kontenerze
execution_repository = providers.Factory(SqlExecutionRepository)

# Użycie — handler dostaje port, nie adapter
class CreateExecutionHandler:
    def __init__(self, repository: ExecutionRepository) -> None:
        self._repository = repository  # Nie wie czy SQL, InMemory czy mock
```

## 4. Lifecycle Management

| Scope | Kiedy używać | Przykład |
|-------|-------------|----------|
| **Singleton** (`providers.Singleton`) | Stateless, thread-safe, współdzielony | Domain Services, Factory, Clock, IdGenerator |
| **Transient** (`providers.Factory`) | Nowa instancja za każdym razem | Handler, Mapper, Repository |
| **Scoped** | Jedna instancja na request/transakcję | Unit of Work, Session |

```python
# shell/bootstrap/platform/container/core_container.py
from dependency_injector import containers, providers

from shell.domain.platform.ports.clock import Clock
from shell.infrastructure.platform.time.system_clock import SystemClock
from shell.domain.platform.ports.id_generator import IdGenerator
from shell.infrastructure.platform.identity.uuid_id_generator import UuidIdGenerator


class CoreContainer(containers.DeclarativeContainer):
    # Singleton — globalnie współdzielone
    clock = providers.Singleton(SystemClock)
    id_generator = providers.Singleton(UuidIdGenerator)
```

## 5. Rejestracja Handlerów przez Factory

Handlery są rejestrowane przez **factory** — kontener tworzy je z wszystkimi zależnościami.

```python
class ExecutionContainer(containers.DeclarativeContainer):
    # Handler — transient (Factory), tworzony na każde wywołanie
    create_execution_handler = providers.Factory(
        CreateExecutionHandler,
        repository=execution_repository,
    )

# Użycie w main.py
handler = container.create_execution_handler()
await handler.handle(command)
```

## 6. Testowanie z Kontenerem

W testach używamy kontenera z nadpisanymi rejestracjami (InMemory zamiast SQL).

```python
# tests/conftest.py
from dependency_injector import containers, providers
from unittest.mock import MagicMock


@pytest.fixture
def test_container() -> containers.DeclarativeContainer:
    class TestContainer(containers.DeclarativeContainer):
        # Nadpisz porty implementacjami InMemory
        execution_repository = providers.Factory(InMemoryExecutionRepository)
        graph_repository = providers.Factory(InMemoryGraphRepository)
        unit_of_work = providers.Factory(InMemoryUnitOfWork)

        # Domain Services — bez zmian (czysta logika)
        execution_creation_service = providers.Singleton(ExecutionCreationService)

        # Handler
        create_execution_handler = providers.Factory(
            CreateExecutionHandler,
            repository=execution_repository,
        )

    return TestContainer()


@pytest.mark.integration
@pytest.fixture
def real_container(db_session: AsyncSession) -> containers.DeclarativeContainer:
    class RealContainer(containers.DeclarativeContainer):
        # Prawdziwe repozytoria z bazą
        execution_repository = providers.Factory(
            SqlExecutionRepository,
            db_session,
            ExecutionMapper(),
        )

        # Domain Services — bez zmian
        execution_creation_service = providers.Singleton(ExecutionCreationService)

        # Handler
        create_execution_handler = providers.Factory(
            CreateExecutionHandler,
            repository=execution_repository,
        )

    return RealContainer()
```

## 7. Główny Composition Root (main.py)

```python
# shell/bootstrap/main.py
from dependency_injector import containers, providers

from shell.bootstrap.platform.container.core_container import CoreContainer
from shell.bootstrap.platform.container.application_container import ApplicationContainer
from shell.bootstrap.execution.container.execution_core_container import ExecutionContainer


class AppContainer(containers.DeclarativeContainer):
    # Agregacja sub-kontenerów
    core = providers.Container(CoreContainer)
    application = providers.Container(ApplicationContainer)
    execution = providers.Container(ExecutionContainer)


def create_container() -> AppContainer:
    return AppContainer()
```

## 8. Zakaz Service Locator

Nigdy nie używaj kontenera jako Service Locator w kodzie produkcyjnym. Kontener jest używany TYLKO w Composition Root.

```python
# ŹLE — Service Locator antypattern
class CreateExecutionHandler:
    async def handle(self, command: CreateExecutionCommand) -> None:
        repository = container.execution_repository()  # ŹLE!
        ...

# DOBRZE — Dependency Injection
class CreateExecutionHandler:
    def __init__(self, repository: ExecutionRepository) -> None:  # DOBRZE
        self._repository = repository
```

## 9. Konfiguracja a DI

Konfiguracja (env, settings) jest ładowana w Composition Root i wstrzykiwana tam, gdzie potrzebna.

```python
# shell/bootstrap/execution/container/execution_core_container.py
class ExecutionContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    execution_factory = providers.Singleton(
        ExecutionFactory,
        max_retries=config.execution.max_retries,
        default_timeout=config.execution.default_timeout,
    )
```

## 10. Podsumowanie — Checklista

Konfigurując DI:
- [ ] Composition Root w `shell/bootstrap/` — jedyne miejsce tworzenia zależności
- [ ] Kontener per Bounded Context w `bootstrap/<bc>/container/`
- [ ] Porty rejestrowane z konkretnymi adapterami (`providers.Factory`)
- [ ] Singleton (`providers.Singleton`) dla stateless serwisów
- [ ] Transient (`providers.Factory`) dla handlerów i mapperów
- [ ] Brak Service Locator w kodzie produkcyjnym
- [ ] Testy używają kontenera z nadpisanymi rejestracjami
- [ ] Konfiguracja ładowana w Composition Root
- [ ] Factory dla handlerów przez kontener
