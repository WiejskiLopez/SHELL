# CQRS Buses

## Cel / Co realizuje

Implementuje podział wiadomości aplikacyjnych na trzy osobne kanały CQRS/EDA:
`CommandBus` (komendy — write side), `QueryBus` (zapytania — read side) oraz
`EventBus` (zdarzenia domenowe — integracja). Obok nich istnieje `MessageBus`
dla wiadomości niebędących zdarzeniami. Wszystkie busy to cienkie rejestry
handlerów rozwiązujące handler w momencie dispatch/publish — nie zawierają
logiki biznesowej ani transakcyjności.

## Problem

W systemie z wieloma bounded contextami przesyłanie komunikatów wymaga
jawnie rozdzielonych ścieżek:

- komenda modyfikuje stan i ma dokładnie **jednego** handlera;
- zapytanie czyta dane (read model) i ma **jednego** handlera;
- zdarzenie jest publikowane do **wielu** subskrybentów (fan-out);
- message ma **jednego** konsumenta.

Wspólny, generyczny "bus na wszystko" mieszałby semantykę read/write i nie
pozwalałby egzekwować reguły "1 komenda = 1 handler" vs "1 zdarzenie = N
subskrybentów".

## Realizacja techniczna

Wszystkie busy mieszkają w `shell/platform/application/bus/`. Każdy trzyma
słownik `dict[type, Callable[[], Any]]` z **faktoryjami handlerów** (handler
jest tworzony na każde wywołanie — bezstanowość handlerów) i rozwiązuje handler
po `type(message)` w momencie dispatch.

- `CommandBus` (`command_bus.py`):
  - `register(command_type, factory)` — zapisuje faktoryę dla typu komendy;
  - `async dispatch(command) -> Any` — `factory = self._handler_factories[type(command)]`,
    tworzy handler i `return await handler.handle(command)`.
- `QueryBus` (`query_bus.py`):
  - analogiczna budowa (pole `_factories`), `async dispatch(query) -> Any` —
    jedyna różnica semantyczna: kanał read-only, handler nie modyfikuje stanu.
- `EventBus` (`event_bus.py`):
  - `subscribe(event_type, factory)` — do listy faktoryj danego typu (fan-out),
    `self._handler_factories[event_type].append(factory)`;
  - `async publish(events: Sequence[Any]) -> None` — iteruje zdarzenia i dla
    każdego wywołuje `handler.handle(event)` na wszystkich subskrybentach.
- `MessageBus` (`message_bus.py`):
  - `register(message_type, factory)` + `async dispatch(message) -> None` —
    jeden handler na typ, analogicznie do `CommandBus`, ale bez wartości zwrotnej.

Adaptery portów publikacji (`messaging.py`):

- `EventBusPublisher` (`event_bus_publisher.py`) — adaptuje `EventBus` do portu
  `EventPublisher`; `async publish(events: Sequence[object])` deleguje wprost do
  `self._event_bus.publish(events)`.
- `MessageBusPublisher` (`message_bus_publisher.py`) — adaptuje `MessageBus` do
  portu `MessagePublisher`; `publish` iteruje `messages` i dla każdego wykonuje
  `await self._message_bus.dispatch(message)`.

Kontener busów: `Buses` (`bootstrap/buses/buses.py`) — instancjonuje
`CommandBus()`, `QueryBus()`, `EventBus()`, `MessageBus()` jako współdzielone
obiekty aplikacji.

Separacja read/write:
- write side: `CommandBus.dispatch` kończy się na handlerze komendy, który
  pracuje na `UnitOfWork` i stageuje zdarzenia do outboxu;
- zdarzenia z outboxu są podnoszone przez relay i dostarczane przez transport
  do inboxa, skąd trafiają do `EventBus` (`EventBusPublisher`) jako integracja —
  patrz [delivery-overview](delivery-overview.md) i [relay](relay.md);
- read side: `QueryBus.dispatch` obsługuje wyłącznie zapytania czytające
  (QueryService/read model), bez mutacji stanu.

## Kluczowe pliki

- `shell/platform/application/bus/command_bus.py`
- `shell/platform/application/bus/query_bus.py`
- `shell/platform/application/bus/event_bus.py`
- `shell/platform/application/bus/message_bus.py`
- `shell/platform/application/bus/event_bus_publisher.py`
- `shell/platform/application/bus/message_bus_publisher.py`
- `shell/platform/application/bus/__init__.py`
- `shell/platform/bootstrap/buses/buses.py`
- `shell/platform/application/ports/messaging.py`

## Powiązane koncepcje

- [unit-of-work](unit-of-work.md)
- [transactional-outbox](transactional-outbox.md)
- [delivery-overview](delivery-overview.md)
- [domain-event](domain-event.md)
- [domain-message](domain-message.md)
- [ports-and-adapters](ports-and-adapters.md)
