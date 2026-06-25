---
name: query-handler
description: Zasady budowy handlerów zapytań (Query Handlers) — struktura, lokalizacja, read model. Używaj gdy dodajesz nowy query handler, poprawiasz istniejący, albo review'ujesz poprawność handlerów zapytań.
---

# Query Handler — obsługa zapytań

## Definicja

Query Handler to komponent warstwy aplikacyjnej, który przyjmuje zapytanie (Query), odczytuje dane przez QueryService i zwraca DTO/read model. **Nie modyfikuje stanu** — to CQRS read side.

## Lokalizacja

Handlery zapytań znajdują się w katalogu `application/<bounded_context>/query_handlers/`.

```
shell/application/
    execution/
        query_handlers/
            get_workflow_handler.py
            get_session_history_handler.py
            get_task_execution_by_name_handler.py
    definition/
        query_handlers/
            search_similar_handler.py
            get_runner_config_handler.py
```

## Query Service

QueryService to warstwa odczytu (read side) — implementacja w `infrastructure/`, port w domenie. Handler używa QueryService, nigdy bezpośrednio repozytoriów agregatów.

## Rejestracja

Rejestracja odbywa się w kontenerze DI (dependency_injection).
