---
name: domain-event-handler
description: "Zasady budowy handlerów zdarzeń (Event Handlerów) — struktura, rejestracja, idempotencja, UoW. Używaj gdy dodajesz nowy event handler, poprawiasz istniejący, zmieniasz schemat rejestracji, albo review'ujesz poprawność handlerów."
---

# Event Handler — obsługa faktów (Integration Events)

## Definicja

Event Handler to komponent warstwy aplikacyjnej, który subskrybuje konkretny
**Integration Event** (fakt dostarczony przez inbox/outbox albo wyemitowany
w obrębie BC jako fakt wire) i wykonuje reakcję biznesową. Handler jest
**stateless** — cały stan przechowuje w agregatach.

> Event Handler obsługuje **Integration Events**. Domain Event pozostaje
> wewnętrznym faktem agregatu i dociera do outboxa tylko pod postacią
> Integration Event: `append_event()` → UoW stage'uje → `ReflectiveIntegrationMapper`
> mapuje na Integration Event → `outbox_event`.

## Lokalizacja

Handlery zdarzeń (Integration Events) znajdują się w katalogu `shell/<service>/application/<bounded_context>/<aggregate>/event_handlers/`.

## Rejestracja w EventBus

Rejestracja odbywa się w kontenerze DI danego BC (`shell/<service>/bootstrap/<bc>/container/<bc>_core_container.py`):

```python
event_bus.subscribe(
    AuthSessionCreatedIntegrationEvent,
    container.auth_session_created_event_handler_factory,
)
```

Handler jest wstrzykiwany przez DI (Dependency Injection) — w kontenerze obok rejestracji:

```python
auth_session_created_event_handler_factory = providers.Factory(
    AuthSessionCreatedEventHandler,
    unit_of_work=session_uow_factory,
    clock=clock_factory,
    logger=providers.Object(stdlib_logger),
)
```

Agregat sam zarządza swoim stanem wewnętrznym. Handler jedynie wywołuje metody domenowe, a agregat wewnętrznie (w swojej metodzie biznesowej) wykonuje niezbędne operacje na swoich polach i za pomocą `append_event()` rejestruje zdarzenia domenowe.

## Zakaz bezpośredniego wołania agregatów innych domen

Handler aplikacyjny **nie może bezpośrednio wołać agregatów, serwisów domenowych, repozytoriów ani żadnych innych elementów** należących do innego BC. Zamiast tego używa portu (protokołu) zdefiniowanego w `ports/` danego agregatu lub domenie docelowej.

## Powiązane skille

- `platform/domain-layer/domain-event/SKILL.md` — definiowanie eventów domenowych
- `platform/shell-specific/shell-architecture/references/application.md` — UoW, CQRS
- `platform/integration-patterns/event-driven-integration/SKILL.md` — idempotencja, inbox, outbox, DLQ
