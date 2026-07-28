---
name: event-handler-structure
description: Reguły struktury Event Handler — subskrypcja eventów, idempotencja przez inbox, rejestracja w EventBus.
---

# Enterprise Event Handler Structure

> Kompletne reguły struktury Domain Event Handler we wszystkich bounded contextach.
> Wzorzec jest **symetryczny** do Command Handler — analogiczna struktura plików, DI, rejestracja na busie.

---

## Architektura — Command vs Event

| | Command | Event |
|--|---------|-------|
| **Bus** | `CommandBus` w `Buses` | `EventBus` w `Buses` |
| **Message** | `LoginCommand` — `application/.../commands/` | `UserLoginSucceededIntegrationEvent` — `shell/integration_events/` |
| **Handler** | `LoginHandler` — `application/.../command_handlers/` | `UserLoginSucceededHandler` — `application/.../event_handlers/` |
| **DI fabryki** | `Commands` → `login_handler_factory()` | `EventHandlers` → `user_login_succeeded_handler_factory()` |
| **Rejestracja** | `command_factory.py`: `cmd_bus.register(...)` | `event_factory.py`: `event_bus.subscribe(...)` |

---

## Opublikowany język (Published Language)

Komunikacja między Bounded Contextami odbywa się przez **wspólne integration events** w `shell/integration_events/`. To jest "Published Language" z DDD — oficjalny kontrakt między BC, używający **tylko primitive typów** (str, int, bool). Żadne VOs domenowe nie przekraczają granic BC.

### Zasady

1. Integration event rozszerza `DomainEvent` (żeby przejść przez outbox/inbox pipeline)
2. Używa tylko `str`, `int`, `bool`, `datetime` — nigdy VOs z żadnego BC
3. Definiowany JEDEN RAZ w `shell/integration_events/`
4. Producent i konsument importują z tego samego miejsca
5. Żadnego ACL, żadnego mapowania

### Przykład

```python
# shell/integration_events/user_login_succeeded_integration_event.py
@dataclass(frozen=True, slots=True)
class UserLoginSucceededIntegrationEvent(DomainEvent):
    user_id: str
```

```python
# Producent (User BC, LoginHandler)
from shell.integration_events.user_login_succeeded_integration_event import (
    UserLoginSucceededIntegrationEvent,
)
event = UserLoginSucceededIntegrationEvent(
    user_id=user.id,
    occurred_at=OccurredAt.from_datetime(self._clock.now()),
)
unit_of_work.stage_events([event])
```

```python
# Konsument (Session BC, UserLoginSucceededHandler)
from shell.integration_events.user_login_succeeded_integration_event import (
    UserLoginSucceededIntegrationEvent,
)
if TYPE_CHECKING:
    from shell.integration_events.user_login_succeeded_integration_event import (
        UserLoginSucceededIntegrationEvent,
    )
```

## Pełny przepływ eventu

```
Handler źródłowy (np. LoginHandler)
  → stage_events([UserLoginSucceededIntegrationEvent])
    → UoW commit → serializacja → outbox_event (DB)
      → OutboxToInboxRelay → inbox_event (DB)
        → InboxProcessor.run_once()
          1. SELECT z inbox_event WHERE processed_at IS NULL
          2. EventDeserializer.deserialize(event_type, payload)
          3. row.processed_at = now
          4. session.commit() (najpierw mark processed)
          5. await self._event_bus.publish([integration_event])
               ↓
              EventBus.publish([event])
               ↓
              handler = factory()
              await handler.handle(event)
```

---

## Lokalizacja

```
shell/application/<bounded_context>/<aggregate>/event_handlers/
                                    ↑ obok command_handlers/
```

Przykład:
```
shell/application/session/session/event_handlers/user_login_succeeded_handler.py
shell/application/session/session/event_handlers/__init__.py
```

---

## Klasa

- Import eventu w TYPE_CHECKING — typ używany tylko w sygnaturze `handle()`.
- Porty repozytoriów i serwisów w TYPE_CHECKING.
- Zależności infrastrukturalne wstrzykiwane przez DI.

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.session.aggregates.session import Session
from shell.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)
from shell.domain.session.aggregates.session.value_objects.session_id import SessionId
from shell.domain.session.value_objects.user_id_ref import UserIdRef
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.integration_events.user_login_succeeded_integration_event import (
        UserLoginSucceededIntegrationEvent,
    )
    from shell.platform.application.ports.ports import Clock, IdGenerator, UnitOfWork
```

---

## Metoda `handle`

- Pojedyncza `async handle(self, event: TEvent) -> None`.
- Zwraca `None` — event handlery są fire-and-forget.

---

## Struktura metody — wzorzec

```python
class UserLoginSucceededHandler:
    def __init__(self, unit_of_work: UnitOfWork, clock: Clock, id_generator: IdGenerator) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator

    async def handle(self, event: UserLoginSucceededIntegrationEvent) -> None:
        user_id_ref = UserIdRef(event.user_id)
        now = CreatedAt.from_datetime(self._clock.now())

        async with self._unit_of_work as unit_of_work:
            existing = await unit_of_work.repository(SessionRepository).get_open_by_user_id(
                user_id_ref
            )

            if existing is not None:
                existing.update(UpdatedAt.from_datetime(now.value))
                await unit_of_work.save(SessionRepository, existing)
            else:
                session_id = self._id_generator.new_id(SessionId)
                session = Session.open(id_=session_id, user_id=user_id_ref, now=now)
                await unit_of_work.save(SessionRepository, session)
```

---

## UoW

- `async with self._unit_of_work as unit_of_work:` — UoW jako async context manager.
- `commit()` na `__aexit__` jeśli brak wyjątku; `rollback()` jeśli wyjątek.
- `stage_events(aggregate.pull_events())` jest automatyczne przez `unit_of_work.save()`.

---

## Logowanie

- Handler nie loguje na poziomie biznesowym.
- Duplicate event detection logowany przez InboxProcessor (infrastruktura).
- Logowanie błędów infrastrukturalnych poza handlerem (middleware/pipeline).

---

## Cross-BC

### Published Language (rekomendowane)

- Cross-BC komunikacja przez **wspólne integration events** w `shell/integration_events/`
- Integration event używa tylko primitive typów (`str`, `int`, `bool`)
- Producent i konsument importują z `shell.integration_events`
- **Żadnego ACL, żadnego mapowania, żadnego cross-BC importu domeny**

### Kompozycyjny korzeń (`event_factory.py`)

```python
from shell.integration_events.user_login_succeeded_integration_event import (
    UserLoginSucceededIntegrationEvent,
)

def register_events(core_container):
    event_bus.subscribe(
        UserLoginSucceededIntegrationEvent,
        event_handlers.user_login_succeeded_handler_factory,
    )
```

### Konwersja na referencję

```python
# w handlerze docelowego BC
user_id_ref = UserIdRef(event.user_id)  # str → UserIdRef
```

---

## Rejestracja w DI

### 1. Klasa fabryk w CoreContainer (`core_container.py`)

```python
class EventHandlers:
    """Container for event handler factories."""

    def __init__(self, buses: Buses, infra: Infrastructure) -> None:
        self._buses = buses
        self._infra = infra

    def user_login_succeeded_handler_factory(self) -> UserLoginSucceededHandler:
        from shell.application.session.session.event_handlers.user_login_succeeded_handler import (
            UserLoginSucceededHandler,
        )

        return UserLoginSucceededHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
            id_generator=self._infra.id_generator_factory(),
        )
```

### 2. W `Application.__init__`

```python
class Application:
    def __init__(self, infra: Infrastructure) -> None:
        self.buses = Buses()
        self.commands = Commands(buses=self.buses, infra=infra)
        self.queries = Queries(infra=infra)
        self.event_handlers = EventHandlers(buses=self.buses, infra=infra)
```

---

## Rejestracja na EventBus (`event_factory.py`)

```python
from shell.integration_events.user_login_succeeded_integration_event import (
    UserLoginSucceededIntegrationEvent,
)

def register_events(core_container: CoreContainer) -> None:
    event_bus = core_container.app.buses.event_bus
    event_handlers = core_container.app.event_handlers

    event_bus.subscribe(
        UserLoginSucceededIntegrationEvent,
        event_handlers.user_login_succeeded_handler_factory,
    )
```

---

## Nazewnictwo

| Element | Wzorzec | Przykład |
|---------|---------|----------|
| **Katalog** | `event_handlers/` | `session/session/event_handlers/` |
| **Plik** | `<event_name_in_snake_case>_handler.py` | `user_login_succeeded_handler.py` |
| **Klasa** | `<EventName>Handler` | `UserLoginSucceededHandler` |
| **DI metoda** | `<event_name_in_snake_case>_handler_factory` | `user_login_succeeded_handler_factory` |

Nazwa handlera = nazwa eventu bez `Event` + `Handler`:
- `WorkflowStartedEvent` → `WorkflowStartedHandler`
- `UserLoginSucceededEvent` → `UserLoginSucceededHandler`
- `SessionOpenedEvent` → `SessionOpenedHandler`

---

## Agregat nie istnieje — tworzenie vs błąd

- Jeśli event jest **triggerem utworzenia agregatu** (np. login → session) — brak istniejącego agregatu jest normalnym przypadkiem: **utwórz nowy**.
- Jeśli event jest **reakcją na zmianę istniejącego agregatu** (np. `WorkflowStarted` → task execution) — brak agregatu to błąd: **rzuć wyjątek**.

Decyzja należy do analizy biznesowej — wzorzec nie narzuca jednej ścieżki.

---

## Orkiestracja — Event Chain vs Saga

### Event Chain (choreografia) — gdy 1 handler modyfikuje 1 agregat

Handler A reaguje na event → modyfikuje agregat A → emituje event → Handler B → modyfikuje agregat B.

### Saga (orkiestracja) — gdy potrzeba koordynacji wielu agregatów

1. Event trafia do Process Managera (Saga)
2. Saga emituje osobne **komendy** — każda modyfikuje dokładnie 1 agregat
3. Każdy agregat odpowiada eventem do sagi
4. Saga po zebraniu odpowiedzi emituje event końcowy

---

## Zasady enterprise

1. **Symetria z Command Handler**: event handlery mają identyczną strukturę, DI i rejestrację jak command handlery.
2. **Idempotentność**: EventBus nie gwarantuje exactly-once. Handler musi być idempotentny — InboxProcessor zapewnia to przez `processed_at`.
3. **Jeden agregat na handler**: handler modyfikuje maksymalnie jeden agregat domenowy.
4. **Brak logiki biznesowej**: handler deleguje decyzje biznesowe do agregatu. Wyjątek: **wybór między ścieżkami** (create vs update) to orkiestracja aplikacyjna, nie logika biznesowa.
5. **Cross-BC przez Published Language**: komunikacja między BC przez wspólne integration events w `shell/integration_events/`. Tylko primitive typy — żadne VOs domenowe nie przekraczają granic BC.
6. **Event registry**: każdy DomainEvent (w tym integration events) musi być w `build_event_registry()` w `shell/platform/infrastructure/serialization/event_registry.py`, inaczej deserializacja w InboxProcessor nie znajdzie klasy.
7. **Mapper — `ReflectiveIntegrationMapper`**: jeden mapper w `shell/platform/infrastructure/mapping/reflective_integration_mapper.py`. Używa `importlib` + `dataclasses.fields()` do reflectywnego mapowania dowolnego domain event → integration event. Zero per-aggregate mapperów, zero `isinstance`, zero `try/except`.
8. **UoW integration**: `SqlAlchemyUnitOfWorkBase.save()` wspiera opcjonalny `mapper` — `ReflectiveIntegrationMapper` wstrzyknięty w `core_container.py` na poziomie `Infrastructure.unit_of_work_factory`.
