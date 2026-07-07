---
name: query-handler
description: Zasady budowy handlerów zapytań (Query Handlers) — struktura, lokalizacja, read model. Używaj gdy dodajesz nowy query handler, poprawiasz istniejący, albo review'ujesz poprawność handlerów zapytań.
---

# Query Handler — obsługa zapytań

## Definicja

Query Handler to komponent warstwy aplikacyjnej, który przyjmuje zapytanie (Query), odczytuje dane przez QueryService i zwraca DTO/read model. **Nie modyfikuje stanu** — to CQRS read side.

## Lokalizacja

Handlery zapytań znajdują się w katalogu `application/<bounded_context>/<aggregate>/query_handlers/`.

```
shell/application/
    execution/
        node_execution/
            query_handlers/
                get_node_execution_handler.py
                list_node_executions_handler.py
        task_execution/
            query_handlers/
                get_task_execution_handler.py
        workflow/
            query_handlers/
                get_workflow_handler.py
    definition/
        graph_definition/
            query_handlers/
                get_graph_definition_handler.py
        rag_document/
            query_handlers/
                search_similar_handler.py
```

## Query Handler — reguły

QueryHandler używa bezpośrednio repozytoriów (read model) lub QueryService — nigdy nie modyfikuje stanu. Query jest read-only, zwraca DTO.

## Rejestracja

Rejestracja odbywa się w kontenerze DI (dependency_injection).
