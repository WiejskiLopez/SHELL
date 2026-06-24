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

## Struktura handlera

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.platform.ports.logging import Logger

class GetWorkflowHandler:
    def __init__(self, query_service: WorkflowQueryService, logger: Logger) -> None:
        self._query_service = query_service
        self._logger = logger

    async def handle(self, query: GetWorkflowQuery) -> WorkflowDto | None:
        return await self._query_service.get_by_id(query.workflow_id)
```

## Zasady

1. **Jeden handler = jedno zapytanie** — nigdy nie obsługuj wielu zapytań w jednym handlerze
2. **Bez efektów ubocznych** — handler zapytania NIGDY nie modyfikuje stanu (brak UoW, brak stage_events)
3. **Stateless** — handler nie przechowuje stanu między wywołaniami
4. **Zwraca DTO / read model** — nigdy encji domenowych (to narusza warstwy)
5. **QueryService w TYPE_CHECKING** — serwis odczytu wstrzykiwany przez DI

## Query Service

QueryService to warstwa odczytu (read side) — implementacja w `infrastructure/`, port w domenie. Handler używa QueryService, nigdy bezpośrednio repozytoriów agregatów.

## Rejestracja

Rejestracja odbywa się w kontenerze DI (dependency_injection).
