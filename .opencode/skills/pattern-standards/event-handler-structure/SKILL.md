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
| **Message** | `LoginCommand` — `application/.../commands/` | `UserLoginSucceededIntegrationEvent` — `application/.../integration_events/` |
| **Handler** | `LoginHandler` — `application/.../command_handlers/` | `UserLoginSucceededHandler` — `application/.../event_handlers/` |
| **DI fabryki** | `Commands` → `login_handler_factory()` | `EventHandlers` → `user_login_succeeded_handler_factory()` |
| **Rejestracja** | `command_factory.py`: `cmd_bus.register(...)` | `event_factory.py`: `event_bus.subscribe(...)` |

---

## Integration Events — per‑BC

Integracja między Bounded Contextami odbywa się przez **integration events** definiowane **per BC** w `shell/application/<bc>/<aggregate>/integration_events/`. Każdy BC posiada własne integration events — nie ma wspólnego katalogu.

### Zasady

1. Integration event rozszerza `IntegrationEvent` (klasa w `shell/platform/application/events/integration_event.py`)
2. Używa tylko `str`, `int`, `bool`, `datetime` — nigdy VOs domenowych
3. Definiowany w `shell/application/<produkujący_bc>/<aggregate>/integration_events/`
4. Konsument importuje z tego samego miejsca (produkujący BC jest właścicielem DTO)
5. Mapaowanie domain → integration event robi `ReflectiveIntegrationMapper` automatycznie

```python
# shell/application/user/user/integration_events/user_login_succeeded_integration_event.py
@dataclass(frozen=True, slots=True)
class UserLoginSucceededIntegrationEvent(IntegrationEvent):
    event_id: str
    correlation_id: str
    causation_id: str
    occurred_at: datetime
    aggregate_id: str
    aggregate_name: str
    schema_version: int
    user_id: str
```

> **Uwaga**: pola `event_id`–`schema_version` to envelope dziedziczony z `IntegrationEvent`. W praktyce wypełnia je `ReflectiveIntegrationMapper` — handler nie tworzy integration eventów ręcznie.

## Pełny przepływ eventu

```
Handler źródłowy (np. LoginHandler)
  → stage_events([UserLoginSucceededIntegrationEvent])
    → UoW commit → serializacja → outbox_event (DB)
      → EventOutboxToInboxRelay → inbox_event (DB)
         → EventInboxProcessor.run_once()
           1. SELECT z inbox_event WHERE processed_at IS NULL (FOR UPDATE SKIP LOCKED)
           2. EventDeserializer.deserialize(event_type, payload)
           3. set ContextVar (correlation_id, causation_id)
           4. await self._event_bus.publish([integration_event])  ← dispatch FIRST
           5. row.processed_at = now                              ← mark success (lub retry++ przy błędzie)
           6. session.commit()                                    ← COMMIT wszystkich zmian
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

from shell.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)
from shell.domain.session.value_objects.user_id_ref import UserIdRef
from shell.platform.domain.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from shell.application.user.user.integration_events.user_login_succeeded_integration_event import (
        UserLoginSucceededIntegrationEvent,
    )
    from shell.platform.application.ports.ports import Clock, UnitOfWork
```

---

## Metoda `handle`

- Pojedyncza `async handle(self, event: TEvent) -> None`.
- Zwraca `None` — event handlery są fire-and-forget.

---

## Struktura metody — wzorzec

```python
class UserLoginSucceededHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        session_service: SessionManagementService,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._session_service = session_service

    async def handle(self, event: UserLoginSucceededIntegrationEvent) -> None:
        user_id_ref = UserIdRef(event.user_id)
        now_dt = self._clock.now()

        async with self._unit_of_work as unit_of_work:
            existing = await unit_of_work.repository(SessionRepository).get_open_by_user_id(
                user_id_ref
            )
            session = self._session_service.ensure_open(
                user_id_ref=user_id_ref,
                now_dt=now_dt,
                existing=existing,
            )
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
- Duplicate event detection logowany przez EventInboxProcessor (infrastruktura).
- Logowanie błędów infrastrukturalnych poza handlerem (middleware/pipeline).

---

## Cross-BC

### Mechanizm integracji

Cross-BC komunikacja przez **integration events** — per‑BC DTO w `shell/application/<produkujący_bc>/<aggregate>/integration_events/`:

1. Domain event emitowany przez agregat w BC A
2. `ReflectiveIntegrationMapper` (w `SqlAlchemyUnitOfWorkBase.save()`) mapuje domain event → integration event (wypełnia envelope + konwertuje VOs na stringi)
3. Integration event zapisywany do `outbox_event` w tej samej transakcji
4. `EventOutboxToInboxRelay` → `EventInboxProcessor` → `EventBus` → handler w BC B

Integration event używa tylko primitive typów (`str`, `int`, `bool`, `datetime`). Właścicielem DTO jest produkujący BC.

### Kompozycyjny korzeń (`event_factory.py`)

```python
from shell.application.user.user.integration_events.user_login_succeeded_integration_event import (
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
            session_service=self._infra.session_management_service_factory(),
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
from shell.application.user.user.integration_events.user_login_succeeded_integration_event import (
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
2. **Idempotentność**: EventBus nie gwarantuje exactly-once. Handler musi być idempotentny — EventInboxProcessor zapewnia to przez `processed_at`.
3. **Jeden agregat na handler**: handler modyfikuje maksymalnie jeden agregat domenowy.
4. **Brak logiki biznesowej**: handler deleguje decyzje biznesowe do agregatu. Wyjątek: **wybór między ścieżkami** (create vs update) to orkiestracja aplikacyjna, nie logika biznesowa.
5. **Cross-BC przez integration events**: komunikacja między BC przez integration events per‑BC w `shell/application/<bc>/<aggregate>/integration_events/`. Tylko primitive typy — żadne VOs domenowe nie przekraczają granic BC. Mapowanie domain→integration robi `ReflectiveIntegrationMapper`.
6. **Event registry**: każdy DomainEvent (w tym integration events) musi być w `build_event_registry()` w `shell/platform/infrastructure/serialization/event_registry.py`, inaczej deserializacja w EventInboxProcessor nie znajdzie klasy.
7. **Mapper — `ReflectiveIntegrationMapper`**: jeden mapper w `shell/platform/infrastructure/mapping/reflective_integration_mapper.py`. Używa `importlib` + `dataclasses.fields()` do reflectywnego mapowania dowolnego domain event → integration event. Zero per-aggregate mapperów, zero `isinstance`, zero `try/except`.
8. **UoW integration**: `SqlAlchemyUnitOfWorkBase.save()` wspiera opcjonalny `mapper` — `ReflectiveIntegrationMapper` wstrzyknięty w `core_container.py` na poziomie `Infrastructure.unit_of_work_factory`.
