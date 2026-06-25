---
name: query-handler-structure
description: Reguły struktury Query Handler — read-only, QueryService, zwraca DTO, zakaz modyfikacji stanu.
---

# Query Handler Structure

> Reguły struktury Query Handler we wszystkich bounded contextach.

## Definicja

- Query Handler to komponent warstwy aplikacyjnej, który przyjmuje zapytanie (Query), odczytuje dane przez QueryService i zwraca DTO/read model.
- Nie modyfikuje stanu — to CQRS read side.

## Klasa

- Zależności wstrzykiwane przez konstruktor.
- QueryService w TYPE_CHECKING.

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.workflow.query_services import WorkflowQueryService
```

## Metoda handle

- Pojedyncza `async handle(self, query: TQuery) -> TDto | list[TDto] | None`.
- Zwraca DTO/read model — nigdy encji domenowych (to narusza warstwy).

```python
async def handle(self, get_workflow_query: GetWorkflowQuery) -> WorkflowDto | None:
    return await self._query_service.get_by_id(get_workflow_query.workflow_id)
```

## Bez side effects

- Handler zapytania NIGDY nie modyfikuje stanu.
- Brak UoW, brak `stage_events`, brak zapisów.
- Tylko odczyt.

## Stateless

- Handler nie przechowuje stanu między wywołaniami.

## Lokalizacja

- `shell/application/<bc>/query_handlers/`
