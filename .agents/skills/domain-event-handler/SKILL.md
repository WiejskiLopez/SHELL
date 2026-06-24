---
name: domain-event-handler
description: Zasady budowy handlerów zdarzeń domenowych — nazewnictwo, struktura, rejestracja, idempotencja, UoW.
Używaj gdy dodajesz nowy event handler, poprawiasz istniejący, zmieniasz schemat rejestracji, albo review'ujesz poprawność handlerów.
---

# Domain Event Handler — aplikacyjne obsługa zdarzeń

## Definicja

Event Handler to komponent warstwy aplikacyjnej, który subskrybuje konkretny Domain Event i wykonuje reakcję biznesową. Handler jest **stateless** — cały stan przechowuje w agregatach.

## Lokalizacja

Handlery zdarzeń domenowych znajdują się w katalogu `application/<bounded_context>/event_handlers/`.

## Nazewnictwo

### Główny handler (main)

Jeden event może mieć wielu subskrybentów. **Tylko jeden** (główny) przyjmuje nazwę zgodną z eventem.

```
Plik:  <domain_event_name>_handler.py
Klasa: <DomainEventName>Handler
```

Przykłady:
- `GraphNodeExecutionTimedOutEvent` → plik `graph_node_execution_timed_out_handler.py` → klasa `GraphNodeExecutionTimedOutHandler`
- `GraphExecutionCreatedEvent` → plik `graph_execution_created_handler.py` → klasa `GraphExecutionCreatedHandler`

### Handler wtórny (secondary)

Gdy jeden event ma wielu subskrybentów, dodatkowe handlery otrzymują kwalifikator biznesowy:

```
Plik:  <domain_event_name>_<qualifier>_handler.py
Klasa: <DomainEventName><Qualifier>Handler
```

Przykłady:
- `GraphNodeExecutionCompletedEvent` (main) → `GraphNodeExecutionCompletedHandler`
- `GraphNodeExecutionCompletedEvent` (secondary — propagacja outputu) → `propagate_node_output_to_graph_input.py` → **`graph_node_execution_completed_propagate_output_handler.py`** → `GraphNodeExecutionCompletedPropagateOutputHandler`
- `GraphNodeExecutionCompletedEvent` (secondary — planner) → `planner_result_handler.py` → **`graph_node_execution_completed_planner_handler.py`** → `GraphNodeExecutionCompletedPlannerHandler`

## Struktura handlera

```python
from __future__ import annotations
from typing import TYPE_CHECKING
from shell.domain.execution.aggregates.some_aggregate.events.some_event import SomeEvent

if TYPE_CHECKING:
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork

class SomeEventHandler:
    def __init__(self, uow: UnitOfWork, clock: Clock, logger: Logger) -> None:
        self._uow = uow
        self._clock = clock
        self._logger = logger

    async def handle(self, event: SomeEvent) -> None:
        async with self._uow as uow:
            aggregate = await uow.some_repo.get_by_id(event.aggregate_id)
            if aggregate is None:
                self._logger.warning("...")
                return
            aggregate.do_something(self._clock.now())
            await uow.some_repo.save(aggregate)
            uow.stage_events(aggregate.pull_events())
```

## Zasady

1. **Stateless** — handler nie przechowuje stanu między wywołaniami
2. **Idempotentny** — wielokrotne przetworzenie tego samego eventu daje ten sam efekt (sprawdzaj stan agregatu przed mutacją)
3. **stage_events(pull_events())** po każdej mutacji agregatu
4. **Logger** — loguj ostrzeżenia gdy agregat nie istnieje (to normalne przy ostatecznej spójności)
5. **Import eventu w sekcji głównej** (nie w TYPE_CHECKING) — handler jawnie deklaruje jaki event obsługuje
6. **Porty w TYPE_CHECKING** — zależności infrastrukturalne wstrzykiwane przez DI, importowane warunkowo

## Rejestracja w EventBus

Rejestracja odbywa się w `event_factory.py`:

```python
event_bus.subscribe(
    SomeEvent,
    events.some_event_handler_factory,
)
```

Handler jest wstrzykiwany przez DI (Dependency Injection) — fabryka w `EventContainer`:

```python
some_event_handler_factory = providers.Factory(
    SomeEventHandler,
    uow=buses.uow_factory,
    clock=infra.clock_factory,
    logger=infra.stdlib_logger,
)
```

## Metody wywoływane na agregatach w handlerze

Handler **może wywoływać na agregatach wyłącznie metody, których nazwy wyrażają intencję biznesową** — nigdy techniczne operacje (`save`, `update`, `merge`, `persist`).

Agregat sam zarządza swoim stanem wewnętrznym. Handler jedynie wywołuje metody domenowe, a agregat wewnętrznie (w swojej metodzie biznesowej) wykonuje niezbędne operacje na swoich polach i za pomocą `append_event()` rejestruje zdarzenia domenowe.

## Zakaz bezpośredniego wołania agregatów innych domen

Handler aplikacyjny **nie może bezpośrednio wołać agregatów, serwisów domenowych, repozytoriów ani żadnych innych elementów** należących do innej domeny. Zamiast tego używa portu (protokołu) zdefiniowanego w `application/ports/` lub domenie docelowej.

## Powiązane skille

- `.agents/skills/domain-event/SKILL.md` — definiowanie eventów domenowych
- `.agents/skills/shell-architecture/references/application.md` — UoW, CQRS
- `.agents/skills/event-driven-integration/SKILL.md` — idempotencja, inbox, outbox, DLQ
