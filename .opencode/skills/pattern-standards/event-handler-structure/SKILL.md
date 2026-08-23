---
name: event-handler-structure
description: Reguły struktury Event Handler — subskrypcja eventów, idempotencja przez inbox, rejestracja w EventBus.
---

# Enterprise Event Handler Structure

> Kompletne reguły struktury Domain Event Handler we wszystkich bounded contextach.
> Wzorzec jest **symetryczny** do Command Handler — analogiczna struktura plików, DI, rejestracja na busie (patrz `command-handler-structure`).

---

## Architektura — bus

- Event Handler rejestrowany na `EventBus` przez `event_factory.py` (`event_bus.subscribe(...)`).
- Semantyke Event opisuje `architectural-discipline/event-semantics`.

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
- `commit()` na `__aexit__` jeśli brak wyjątku; `rollback()` jeśli wyjątek (patrz `unit-of-work-structure`).

---

## Logowanie

- Handler nie loguje na poziomie biznesowym.
- Logowanie błędów infrastrukturalnych poza handlerem (middleware/pipeline, patrz `middleware-structure`).

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

(Dokladne reguly nazw piszemy tak samo dla klas/funkcji w warstwie application per `naming-standards`.)

---

## Obsluga stanu agregatu — tworzenie vs blad

- Jeśli event jest **triggerem utworzenia agregatu** (np. login → session) — brak istniejącego agregatu jest normalnym przypadkiem: **utwórz nowy**.
- Jeśli event jest **reakcją na zmianę istniejącego agregatu** (np. `WorkflowStarted` → task execution) — brak agregatu to błąd: **rzuć wyjątek**.

Decyzja należy do analizy biznesowej — wzorzec nie narzuca jednej ścieżki.

---

## Komunikacja między BC i orkiestracja

- Cross-BC komunikacja przez **integration events** oraz routing przez outbox/inbox/procesor — opisuje `integration-patterns/event-driven-integration` i `integration-patterns/integration-event`.
- Koordynacja wielu agregatów (Event Chain vs Saga) — opisuje `pattern-standards/saga-structure`.
- Rejestracja handlerów w DI i spójność `.subscribe()` z providerami — opisuje `infrastructure-layer/di-composition-root` i `application-layer/handler-registration-integrity`.

---

## Zasady — własny zakres

1. **Symetria z Command Handler**: event handlery mają identyczną strukturę, DI i rejestrację jak command handlery (patrz `command-handler-structure`).
2. **Idempotentność handlera**: handler nie zakłada exactly-once; dedup dostaw zapewnia infrastruktura (patrz `idempotent-handler-pattern`).
3. **Jeden agregat na handler**: handler modyfikuje maksymalnie jeden agregat domenowy.
4. **Brak logiki biznesowej**: handler deleguje decyzje biznesowe do agregatu. Wyjątek: **wybór między ścieżkami** (create vs update) to orkiestracja aplikacyjna, nie logika biznesowa.
