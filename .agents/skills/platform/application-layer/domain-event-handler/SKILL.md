---
name: domain-event-handler
description: Zasady budowy handlerów zdarzeń domenowych — struktura, rejestracja, idempotencja, UoW.
Używaj gdy dodajesz nowy event handler, poprawiasz istniejący, zmieniasz schemat rejestracji, albo review'ujesz poprawność handlerów.
---

# Domain Event Handler — aplikacyjne obsługa zdarzeń

## Definicja

Event Handler to komponent warstwy aplikacyjnej, który subskrybuje konkretny Domain Event i wykonuje reakcję biznesową. Handler jest **stateless** — cały stan przechowuje w agregatach.

## Lokalizacja

Handlery zdarzeń domenowych znajdują się w katalogu `application/<bounded_context>/event_handlers/`.

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
    unit_of_work=buses.unit_of_work_factory,
    clock=infra.clock_factory,
    logger=infra.stdlib_logger,
)
```

Agregat sam zarządza swoim stanem wewnętrznym. Handler jedynie wywołuje metody domenowe, a agregat wewnętrznie (w swojej metodzie biznesowej) wykonuje niezbędne operacje na swoich polach i za pomocą `append_event()` rejestruje zdarzenia domenowe.

## Zakaz bezpośredniego wołania agregatów innych domen

Handler aplikacyjny **nie może bezpośrednio wołać agregatów, serwisów domenowych, repozytoriów ani żadnych innych elementów** należących do innej domeny. Zamiast tego używa portu (protokołu) zdefiniowanego w `application/ports/` lub domenie docelowej.

## Powiązane skille

- `platform/domain-layer/domain-event/SKILL.md` — definiowanie eventów domenowych
- `platform/shell-specific/shell-architecture/references/application.md` — UoW, CQRS
- `platform/integration-patterns/event-driven-integration/SKILL.md` — idempotencja, inbox, outbox, DLQ
