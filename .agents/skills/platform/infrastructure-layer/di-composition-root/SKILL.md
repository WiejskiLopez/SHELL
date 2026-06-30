---
name: di-composition-root
description: Zasady projektowania Composition Root / Dependency Injection w architekturze hexagonalnej — struktura modułów DI per BC, lifecycle (singleton/transient/scoped), rejestracja port-adapter, factory dla handlerów, testowanie z kontenerem. Używaj gdy konfigurujesz DI dla nowego BC, dodajesz nową rejestrację, albo refaktoryzujesz bootstrap.
---

# DI / Composition Root w Enterprise DDD

## 1. Composition Root — Jedno Miejsce

**Composition Root** to jedyne miejsce w aplikacji, gdzie tworzone są zależności. Znajduje się w `shell/bootstrap/`.

```
shell/bootstrap/
├── main.py                       # Główny composition root
├── modules/                      # Moduły DI per BC
│   ├── __init__.py
│   ├── execution_module.py
│   ├── graph_module.py
│   ├── scheduler_module.py
│   └── shared_module.py
└── containers/
    ├── __init__.py
    └── container.py              # Główny kontener DI
```

## 2. Moduły DI Per Bounded Context

Każdy BC ma własny moduł DI, który rejestruje wszystkie zależności danego kontekstu. Moduły są niezależne.

```python
# shell/bootstrap/modules/execution_module.py
from punq import Container, Scope

from shell.domain.execution.factories.execution_factory import ExecutionFactory
from shell.domain.execution.repositories.execution_repository import ExecutionRepository
from shell.domain.execution.services.execution_creation_service import ExecutionCreationService
from shell.infrastructure.execution.repositories.sql_execution_repository import SqlExecutionRepository
from shell.infrastructure.execution.mappers.execution_mapper import ExecutionMapper


class ExecutionModule:
    """Moduł DI dla Execution Bounded Context."""
    
    @staticmethod
    def register(container: Container) -> None:
        # Port → Adapter
        container.register(
            ExecutionRepository,
            SqlExecutionRepository,
            scope=Scope.transient,
        )

        # Domain Services (singleton — stateless)
        container.register(
            ExecutionCreationService,
            scope=Scope.singleton,
        )

        # Factory (singleton — może mieć stan konfiguracyjny)
        container.register(
            ExecutionFactory,
            scope=Scope.singleton,
        )

        # Mapper (transient — może być współdzielony)
        container.register(
            ExecutionMapper,
            scope=Scope.transient,
        )
```

## 3. Rejestracja Port → Adapter

Każdy port (Protocol/ABC) jest rejestrowany z konkretną implementacją. Dzięki temu kod domenowy nie wie o istnieniu adapterów.

```python
# Rejestracja Port → Adapter
container.register(ExecutionRepository, SqlExecutionRepository)

# Użycie — handler dostaje port, nie adapter
class CreateExecutionHandler:
    def __init__(self, repository: ExecutionRepository) -> None:
        self._repository = repository  # Nie wie czy SQL, InMemory czy mock
```

## 4. Lifecycle Management

| Scope | Kiedy używać | Przykład |
|-------|-------------|----------|
| **Singleton** | Stateless, thread-safe, współdzielony | Domain Services, Factory, Clock, IdGenerator |
| **Transient** | Nowa instancja za każdym razem | Handler, Mapper, Repository |
| **Scoped** | Jedna instancja na request/transakcję | Unit of Work, Session |

```python
# shell/bootstrap/modules/shared_module.py
from punq import Container, Scope

class SharedModule:
    @staticmethod
    def register(container: Container) -> None:
        # Singleton — globalnie współdzielone
        container.register(Clock, SystemClock, scope=Scope.singleton)
        container.register(IdGenerator, UuidIdGenerator, scope=Scope.singleton)

        # Transient — lekki, stan tymczasowy
        container.register(EventBus, scope=Scope.singleton)
```

## 5. Rejestracja Handlerów przez Factory

Handlery są rejestrowane przez **factory** — kontener tworzy je z wszystkimi zależnościami.

```python
class ExecutionModule:
    @staticmethod
    def register(container: Container) -> None:
        # Handler — transient, tworzony na każde wywołanie
        container.register(CreateExecutionHandler, scope=Scope.transient)

# Użycie w main.py
handler = container.resolve(CreateExecutionHandler)
await handler.handle(command)
```

## 6. Testowanie z Kontenerem

W testach używamy kontenera z nadpisanymi rejestracjami (InMemory zamiast SQL).

```python
# tests/conftest.py
@pytest.fixture
def test_container() -> Container:
    container = Container()
    
    # Nadpisz porty implementacjami InMemory
    container.register(ExecutionRepository, InMemoryExecutionRepository, scope=Scope.transient)
    container.register(GraphRepository, InMemoryGraphRepository, scope=Scope.transient)
    container.register(UnitOfWork, InMemoryUnitOfWork, scope=Scope.transient)
    
    # Domain Services — bez zmian (czysta logika)
    container.register(ExecutionCreationService, scope=Scope.singleton)
    
    # Handler
    container.register(CreateExecutionHandler, scope=Scope.transient)
    return container


@pytest.mark.integration
@pytest.fixture
def real_container(db_session: AsyncSession) -> Container:
    container = Container()
    
    # Prawdziwe repozytoria z bazą
    container.register(ExecutionRepository, 
        instance=SqlExecutionRepository(db_session, ExecutionMapper()))
    
    # Reszta bez zmian
    container.register(ExecutionCreationService, scope=Scope.singleton)
    container.register(UnitOfWork, instance=SqlUnitOfWork(db_session))
    container.register(CreateExecutionHandler, scope=Scope.transient)
    return container
```

## 7. Główny Composition Root (main.py)

```python
# shell/bootstrap/main.py
from punq import Container

from shell.bootstrap.modules.execution_module import ExecutionModule
from shell.bootstrap.modules.graph_module import GraphModule
from shell.bootstrap.modules.shared_module import SharedModule


def create_container() -> Container:
    container = Container()
    
    # Kolejność rejestracji nie ma znaczenia
    SharedModule.register(container)
    GraphModule.register(container)
    ExecutionModule.register(container)
    
    return container
```

## 8. Zakaz Service Locator

Nigdy nie używaj kontenera jako Service Locator w kodzie produkcyjnym. Kontener jest używany TYLKO w Composition Root.

```python
# ŹLE — Service Locator antypattern
class CreateExecutionHandler:
    async def handle(self, command: CreateExecutionCommand) -> None:
        repository = container.resolve(ExecutionRepository)  # ŹLE!
        ...

# DOBRZE — Dependency Injection
class CreateExecutionHandler:
    def __init__(self, repository: ExecutionRepository) -> None:  # DOBRZE
        self._repository = repository
```

## 9. Konfiguracja a DI

Konfiguracja (env, settings) jest ładowana w Composition Root i wstrzykiwana tam, gdzie potrzebna.

```python
# shell/bootstrap/modules/execution_module.py
class ExecutionModule:
    @staticmethod
    def register(container: Container, settings: AppSettings) -> None:
        container.register(
            ExecutionFactory,
            instance=ExecutionFactory(
                max_retries=settings.execution.max_retries,
                default_timeout=settings.execution.default_timeout,
            ),
        )
```

## 10. Podsumowanie — Checklista

Konfigurując DI:
- [ ] Composition Root w `shell/bootstrap/` — jedyne miejsce tworzenia zależności
- [ ] Jeden moduł DI per Bounded Context
- [ ] Porty rejestrowane z konkretnymi adapterami
- [ ] Singleton dla stateless serwisów
- [ ] Transient dla handlerów i mapperów
- [ ] Scoped dla UoW i sesji
- [ ] Brak Service Locator w kodzie produkcyjnym
- [ ] Testy używają kontenera z nadpisanymi rejestracjami
- [ ] Konfiguracja ładowana w Composition Root
- [ ] Factory dla handlerów przez kontener
