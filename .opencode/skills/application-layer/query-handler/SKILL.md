---
name: query-handler
description: Zasady budowy handlerów zapytań (Query Handlers) — struktura, lokalizacja, read model. Używaj gdy dodajesz nowy query handler, poprawiasz istniejący, albo review'ujesz poprawność handlerów zapytań.
---

# Query Handler — obsługa zapytań

## Definicja

Query Handler to komponent warstwy aplikacyjnej, który przyjmuje zapytanie (Query), odczytuje dane przez QueryService i zwraca DTO/read model. **Nie modyfikuje stanu** — to CQRS read side.

## Lokalizacja

Handlery zapytań znajdują się w katalogu `shell/<service>/application/<bounded_context>/<aggregate>/query_handlers/`.

```
shell/<service>/application/
    execution/
        task_execution/
            query_handlers/
                get_task_execution_handler.py
        workflow/
            query_handlers/
                get_workflow_handler.py
        edge_execution/
            query_handlers/
                get_edge_execution_handler.py
    definition/
        graph_definition/
            query_handlers/
                get_graph_definition_by_id_handler.py
```

Query Service (port odczytu) leży obok, w `shell/<service>/application/<bc>/<aggregate>/ports/<aggregate>_query_service.py`.

## Query Handler — reguły

QueryHandler używa bezpośrednio QueryService (read model) — nigdy nie modyfikuje stanu. Query jest read-only, zwraca DTO.

## Rejestracja

Rejestracja odbywa się w kontenerze DI danego BC (`shell/<service>/bootstrap/<bc>/container/<bc>_core_container.py`) — każdy handler ma provider `*_handler_factory = providers.Factory(...)`. Textualny wzorzec: patrz `pattern-standards/query-handler-structure`.
