---
name: handler-registration-integrity
description: "Reguły spójności rejestracji handlerów — każdy .subscribe() lub .register() w kontenerze BC musi mieć odpowiadający mu provider `*_handler_factory` w tym samym kontenerze."
---

# Handler Registration Integrity

> Zapewnienie, że każdy handler zarejestrowany w command/query/event bus faktycznie istnieje jako provider w kontenerze DI danego BC.

## Dlaczego to jest potrzebne

W kontenerze BC (np. `shell/<service>/bootstrap/<bc>/container/<bc>_core_container.py`) rejestrujemy handler przez provider oraz subskrypcję na busie:

```python
# ŹLE — brak providera dla handlera
command_bus: CommandBus = providers.Singleton(CommandBus)
...
# subskrypcja przez sam container (app.wiring) odwołuje się do nieistniejącego providera

# DOBRZE
change_workflow_handler_factory = providers.Factory(
    ChangeWorkflowHandler,
    unit_of_work=workflow_uow_factory,
    clock=clock_factory,
)
```

Jeśli `register()/subscribe()` odwoła się do providera, który nie istnieje, w runtime przy bootowaniu aplikacji dostajesz `AttributeError`/błąd rozwiązywania zależności. Ten błąd nie jest wyłapywany przez linter ani type checker — pojawia się dopiero przy próbie utworzenia kontenera.

## Reguła 1: Każdy odwołany provider = istniejąca definicja

Dla każdego `bus.subscribe(<EventName>, <X>_factory)` / `bus.register(<CommandName>, <X>_factory)` w kontenerze BC sprawdź, że w tym samym kontenerze istnieje `X_factory = providers.Factory(...)` (lub `providers.Singleton(...)`).

## Reguła 2: Odwrotna zależność — każdy provider jest zarejestrowany

Każdy provider handlera w kontenerze BC powinien mieć podpiętą subskrypcję/rejestrację na odpowiedni bus. Jeśli provider istnieje ale nie jest zarejestrowany na żaden event/command — to martwy kod.

## Reguła 3: Weryfikacja — test kontenera

Najprostszy test to utworzenie instancji kontenera BC — to sprawdzi, czy wszystkie importy i referencje do providerów są poprawne:

```python
from shell.user_service.bootstrap.user.container.user_core_container import (
    UserCoreContainer,
)

def test_core_container_builds() -> None:
    container = UserCoreContainer()
    container.config.from_dict({"db_url": "sqlite:///:memory:"})
    # Jeśli to nie rzuci AttributeError — wszystkie rejestracje są spójne
```

## Reguła 4: Kontrakt nazewniczy — `<nazwa>_handler_factory`

Wszystkie providery będące fabrykami handlerów używają sufiksu `_handler_factory` (spójnie z realnym kodem: `create_workflow_handler_factory`, `list_workflows_handler_factory`, `get_edge_execution_handler_factory`):

- `create_workflow_handler_factory = providers.Factory(CreateWorkflowHandler, unit_of_work=..., clock=...)` ✅
- `create_workflow_handler = providers.Factory(...)` ❌ (brak sufiksu `_handler_factory`)

## Reguła 5: Brak duplikacji subskrypcji

Nie subskrybuj tego samego eventu dwa razy:

```python
# ŹLE — dwie subskrypcje do GraphExecutionSubGraphSettledEvent
event_bus.subscribe(GraphExecutionSubGraphSettledEvent, events.propagate_subgraph_results_to_parent_factory)
event_bus.subscribe(GraphExecutionSubGraphSettledEvent, events.handle_sub_graph_settled_factory)

# DOBRZE — jedna subskrypcja na event
event_bus.subscribe(GraphExecutionSubGraphSettledEvent, events.propagate_subgraph_results_to_parent_factory)
```

Wyjątek: celowa intencja wielu handlerów na jeden event — wtedy **wszystkie** muszą istnieć jako providery.

## Reguła 6: Weryfikacja testami architektury

Repo zawiera testy strzegące spójności rejestracji (np. `shell/tests/architecture/test_cqrs_query_discipline__testeveryqueryispublishedtothebus_test_all_queries_are_registered.py`, `test_container_delivery_bundle_wiring.py`, `test_bc_container_boundaries.py`). Przed merge sprawdź, czy filtrów rejestracji nie naruszono — patrz też `shell-specific/test-topology`.