---
name: di-composition-root
description: Zasady projektowania Composition Root / Dependency Injection w architekturze hexagonalnej — struktura modułów DI per BC, lifecycle (singleton/factory), rejestracja port-adapter, factory dla handlerów, testowanie z kontenerem. Używaj gdy konfigurujesz DI dla nowego BC, dodajesz nową rejestrację, albo refaktoryzujesz bootstrap.
---

# DI / Composition Root w Enterprise DDD

## 1. Composition Root — jedno miejsce per BC

Composition Root to jedyne miejsce w aplikacji, gdzie tworzone są zależności. W SHELL każdy BC ma **własny** composition root (brak wspólnego `shell/bootstrap/`):

```
shell/<service>/bootstrap/
├── <bc>/                            # DI dla konkretnego BC (np. shell/user_service/bootstrap/user/)
│   └── container/<bc>_core_container.py   # np. user_core_container.py, execution_core_container.py
├── config/
└── cli/
```

Przykład realnej lokalizacji: `shell/user_service/bootstrap/user/container/user_core_container.py`,
`shell/execution_service/bootstrap/execution/container/execution_core_container.py`.

## 2. Moduły DI Per Bounded Context

Każdy BC ma własny `<bc>_core_container`, który rejestruje wszystkie zależności danego kontekstu. Moduły są niezależne.

```python
# shell/execution_service/bootstrap/execution/container/execution_core_container.py
from dependency_injector import containers, providers

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.event_bus import EventBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.time.system_clock import SystemClock
from shell.platform.infrastructure.identity.uuid_id_generator import UuidIdGenerator


class ExecutionCoreContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)

    command_bus = providers.Singleton(CommandBus)
    query_bus = providers.Singleton(QueryBus)
    event_bus = providers.Singleton(EventBus)
```

## 3. Rejestracja Port → Adapter

Każdy port (Protocol) rejestruje się z konkretną implementacją; kod domenowy zna
wyłącznie porty, a wiązanie port→adapter wykonuje Composition Root.

```python
# Rejestracja Port → Adapter w kontenerze BC
graph_definition_provider = providers.Factory(
    GraphDefinitionProviderHttpAdapter,
    client=definition_http_client,
)
```

## 4. Lifecycle Management

Realne konwencje w kontenerach SHELL (`ExecutionCoreContainer`, `UserCoreContainer`):

| Scope | Kiedy używać | Realny przykład w SHELL |
|-------|-------------|----------|
| **Factory** (`providers.Factory`) | Nowa instancja na każde użycie; UoW per operacja, zegar, IdGenerator, handlery | `clock_factory`, `id_generator_factory`, `workflow_uow_factory`, `create_workflow_handler_factory` |
| **Singleton** (`providers.Singleton`) | Stateless, współdzielone, konfiguracja, sesja, busy, registry | `session_factory`, `command_bus`, `query_bus`, `event_bus`, `event_registry` |

Uwaga: UoW rejestrowane jest jako **`providers.Factory`** (nowa instancja per zapis/operację);
Query services często są `providers.Singleton` (stateless, read-only).

## 5. Rejestracja Handlerów przez Factory

Handlery są rejestrowane przez provider z sufiksem `_handler_factory`; wstrzykują UoW, zegar i id_generator.

```python
# w ExecutionCoreContainer
workflow_uow_factory = providers.Factory(
    WorkflowUnitOfWork,  # per-BC UoW z mapą portów → klas SQL
    session_factory=session_factory,
)

create_workflow_handler_factory = providers.Factory(
    CreateWorkflowHandler,
    unit_of_work=workflow_uow_factory,
    clock=clock_factory,
    id_generator=id_generator_factory,
)
```

## 6. Testowanie z Kontenerem

W testach używamy kontenera z nadpisanymi rejestracjami (InMemory zamiast SQL).

```python
# tests/<bc>/conftest.py
@pytest.fixture
def container() -> ExecutionCoreContainer:
    c = ExecutionCoreContainer()
    c.config.from_dict({"db_url": "sqlite:///:memory:"})
    return c
```

Zamiast ręcznie podmieniać providery: UoW danego BC czyta sesję z `session_factory`; dla testów jednostkowych handlera wstrzykuj `InMemory*Repository` bezpośrednio w konstruktorze handlera (patrz `arch-testing/testing`).

## 7. Główny Composition Root (app factory)

Każdy BC wystawia własną fabrykę aplikacji, która tworzy kontener i podpinuje routery;
centralny `main.py` montujący wszystkie BC leży poza strukturą SHELL:

```python
# shell/<service>/framework/<bc>/api/app.py
def create_<bc>_app(container: <Bc>CoreContainer = Depends(get_core_container)) -> FastAPI:
    ...
```

Busy rejestrują handlery w kontenerze lub osobnej funkcji `setup_buses(container)` wywoływanej przy tworzeniu aplikacji:

```python
command_bus.register(OpenSessionCommand, container.open_session_handler_factory)
query_bus.register(GetSessionByIdQuery, container.get_session_by_id_handler_factory)
event_bus.subscribe(AuthSessionCreatedIntegrationEvent, container.auth_session_created_event_handler_factory)
```

## 8. Serwisy: DI vs Service Locator

Kontener pełni rolę **wyłącznie Composition Root**; kod produkcyjny odbiera zależności
przez wstrzykiwanie (DI), a nie przez odpytywanie kontenera.

```python
# Antywzorzec — Service Locator w handlerze
class CreateWorkflowHandler:
    async def handle(self, command: CreateWorkflowCommand) -> None:
        repository = container.workflow_repository()  # Antywzorzec

# Poprawnie — Dependency Injection
class CreateWorkflowHandler:
    def __init__(self, unit_of_work: UnitOfWork) -> None:  # Poprawnie
        self._unit_of_work = unit_of_work
```

## 9. Konfiguracja a DI

Konfiguracja (env, settings) jest ładowana w Composition Root i wstrzykiwana tam, gdzie potrzebna.

```python
# w <bc>_core_container.py
class ExecutionCoreContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    session_factory = providers.Singleton(build_session_factory, url=config.db_url)
```

## 10. Podsumowanie — Checklista

Konfigurując DI:
- [ ] Composition Root per BC w `shell/<service>/bootstrap/<bc>/container/<bc>_core_container.py`
- [ ] Brak top-level `shell/bootstrap/` — każdy BC samodzielny
- [ ] Porty rejestrowane z konkretnymi adapterami (`providers.Factory`/`providers.Singleton`)
- [ ] `providers.Factory` dla UoW, zegara, IdGeneratora i handlerów (`*_handler_factory`)
- [ ] `providers.Singleton` dla busów, session factory i rejestrów
- [ ] Di wstrzykuje zależności w kodzie produkcyjnym; kontener pozostaje w Composition Root
- [ ] Testy używają kontenera z konfiguracją sqlite lub wstrzykują InMemory bezpośrednio
- [ ] Konfiguracja ładowana w kontenerze BC
- [ ] Rejestracja handlerów: `bus.register(<CommandName>, container.<X>_handler_factory)` / `bus.subscribe(...)` — spójność z `application-layer/handler-registration-integrity`