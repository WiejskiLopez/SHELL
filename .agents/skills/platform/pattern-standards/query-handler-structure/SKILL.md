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
- Import query może być w TYPE_CHECKING — używana tylko w sygnaturze `handle()`.

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.workflow.queries.workflow_get_by_id_query import WorkflowGetByIdQuery
    from shell.application.workflow.query_services import WorkflowQueryService
```

## Metoda handle

- Pojedyncza `async handle(self, query: TQuery) -> TDto | list[TDto] | None`.
- Zwraca DTO/read model — nigdy encji domenowych (to narusza warstwy).

```python
async def handle(self, workflow_get_by_id_query: WorkflowGetByIdQuery) -> WorkflowDto | None:
    return await self._query_service.get_by_id(workflow_get_by_id_query.workflow_id)
```

## Query Service — lokalizacja per agregat

Query Service nie jest jeden na cały BC. Służy do czytania danych bezpośrednio przez SQL/ORM (read model), bez łądowania agregatów. Grupuje się je per agregat w folderze `query_services/<nazwa_agregatu>/`:

```
shell/application/<bc>/
    query_services/
        <nazwa_agregatu>/
            <nazwa>_service.py
```

Przykład:

```
shell/application/
    execution/
        query_services/
            workflow/
                workflow_list_service.py
                workflow_detail_service.py
                workflow_summary_service.py
            session/
                session_history_service.py
    definition/
        query_services/
            document/
                document_search_service.py
```

### Zasady

1. **Per agregat, nie per BC** — query services są grupowane po agregacie, nie po bounded context. Folder `query_services/<agregat>/` zawiera wszystkie serwisy odczytu dla danego agregatu.
2. **Łatwa ekstrakcja** — jeśli agregat zostanie wydzielony do osobnego mikroserwisu, cały folder `query_services/<agregat>/` jest przenoszony wraz z handlerami, co minimalizuje koszt migracji.
3. **Jeden serwis = grupa powiązanych zapytań** — serwis może mieć wiele metod (list, detail, history), ale wszystkie dotyczą tego samego read modelu / agregatu.
4. **Bez UoW, bez eventów** — Query Service czyta, nie modyfikuje.
5. **Zwraca DTO** — nigdy encji domenowych.

```python
# shell/application/execution/query_services/workflow/workflow_list_service.py
class WorkflowListService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active(self) -> list[WorkflowSummaryDto]:
        ...

    async def get_by_owner(self, owner_id: UserId) -> list[WorkflowSummaryDto]:
        ...
```

## Bez side effects

- Handler zapytania NIGDY nie modyfikuje stanu.
- Brak UoW, brak `stage_events`, brak zapisów.
- Tylko odczyt.

## Stateless

- Handler nie przechowuje stanu między wywołaniami.

> **Reguły nazewnictwa → [naming-convention-standard](../../naming-standards/naming-convention-standard/SKILL.md#queries)**

## Lokalizacja

- Query Handlers: `shell/application/<bc>/query_handlers/`
- Query Services: `shell/application/<bc>/query_services/<nazwa_agregatu>/`
