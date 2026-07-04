---
name: handler-registration-integrity
description: Reguły spójności rejestracji handlerów — każdy .subscribe() lub .register() w fabrykach musi mieć odpowiadający mu providers.Factory() w kontenerze.
---

# Handler Registration Integrity

> Umiejętność zapewnienia że każdy handler zarejestrowany w command/event bus faktycznie istnieje jako provider w kontenerze DI.

## Dlaczego to jest potrzebne

Gdy `event_factory.py` woła:

```python
event_bus.subscribe(GraphExecutionSubGraphSettledEvent, events.handle_sub_graph_settled_factory)
```

ale w `event_container.py` nie ma:

```python
handle_sub_graph_settled_factory = providers.Factory(...)
```

to w runtime (przy bootowaniu aplikacji) dostajesz:

```
AttributeError: 'DynamicContainer' object has no attribute 'handle_sub_graph_settled_factory'
```

Ten błąd nie jest wyłapywany przez linter ani type checker — pojawia się dopiero przy próbie utworzenia kontenera.

## Reguła 1: Każdy atrybut użyty w fabryce = istniejący provider

Dla każdego wywołania `events.XYZ_factory` lub `commands.XYZ_factory` w plikach:

- `event_factory.py`
- `command_factory.py`
- `query_factory.py`
- `bus_factory.py`

Sprawdź, że w odpowiednim kontenerze (`EventContainer`, `CommandContainer`, `QueryContainer`) istnieje definicja `XYZ_factory = providers.Factory(...)` lub `XYZ_factory = providers.Singleton(...)`.

## Reguła 2: Odwrotna zależność — każdy provider jest gdzieś zarejestrowany

Każdy provider w kontenerze (`command_container.py`, `event_container.py`, itp.) powinien być zarejestrowany w odpowiedniej fabryce (`command_factory.py`, `event_factory.py`).

Jeśli provider istnieje ale nie jest zarejestrowany na żaden event/command — to martwy kod.

## Reguła 3: Weryfikacja — test kontenera

Najprostszy test to stworzenie instancji kontenera — to wywołanie sprawdzi czy wszystkie importy i referencje do providerów są poprawne:

```python
from shell.bootstrap.platform.container.core_container import CoreContainer

def test_core_container_builds():
    container = CoreContainer()
    container.config.from_dict({"database_url": "sqlite:///:memory:"})
    container.init_resources()  # jeśli istnieje
    # Jeśli to nie rzuci AttributeError — wszystkie rejestracje są spójne
```

Jeśli kontener wymaga skomplikowanej konfiguracji, możesz przynajmniej przetestować czy importy i nazwy providerów ładują się poprawnie:

```python
from shell.bootstrap.platform.container.event_container import EventContainer

def test_event_container_has_all_providers():
    """Sprawdź czy EventContainer ma oczekiwane atrybuty factory."""
    container = EventContainer()
    # Symuluj zależności
    container.infra = ...
    container.domain = ...
    container.buses = ...
```

## Reguła 4: Kontrakt nazewniczy — factory suffix

Wszystkie providery w kontenerach które są fabrykami handlerów używają sufiksu `_factory`:

- `node_execution_completed_handler_factory = providers.Factory(...)`
- `log_audit_handler_factory = providers.Factory(...)`

W fabrykach rejestrujących (event_factory.py, command_factory.py, itp.) odwołuj się przez:

- `events.log_audit_handler_factory` ✅
- `events.log_audit_handler` ❌ (brak sufiksu `_factory`)

## Reguła 5: Brak duplikacji subskrypcji

Nie subskrybuj tego samego eventu dwa razy w tej samej fabryce:

```python
# ŹLE — dwie subskrypcje do GraphExecutionSubGraphSettledEvent
event_bus.subscribe(GraphExecutionSubGraphSettledEvent, events.propagate_subgraph_results_to_parent_factory)
event_bus.subscribe(GraphExecutionSubGraphSettledEvent, events.handle_sub_graph_settled_factory)

# DOBRZE — jedna subskrypcja na event
event_bus.subscribe(GraphExecutionSubGraphSettledEvent, events.propagate_subgraph_results_to_parent_factory)
```

Chyba że intencją jest wielu handlerów na jeden event — wtedy WSZYSTKIE muszą istnieć jako providery.
