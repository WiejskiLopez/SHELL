---
name: query-handler-structure
description: Reguły struktury Query Handler — odczyt danych przez QueryService i zwrot DTO.
---

# Query Handler Structure

> Reguły struktury Query Handler we wszystkich bounded contextach.

## Definicja

- Query Handler to komponent warstwy aplikacyjnej, który przyjmuje zapytanie (Query), odczytuje dane przez QueryService i zwraca DTO/read model.
- Odczytuje dane i zwraca DTO jako CQRS read side.

## Klasa

- Zależności wstrzykiwane przez konstruktor.
- QueryService w TYPE_CHECKING.
- Import query może być w TYPE_CHECKING — używana tylko w sygnaturze `handle()`.

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.execution.workflow.queries.workflow_get_by_id_query import WorkflowGetByIdQuery
    from shell.application.execution.workflow.queries.workflow_query_service import WorkflowQueryService
```

## Metoda handle

- Pojedyncza `async handle(self, query: TQuery) -> TDto | list[TDto] | None`.
- Zwraca DTO/read model nalezacy do warstwy aplikacji.

```python
async def handle(self, query: WorkflowGetByIdQuery) -> WorkflowDto | None:
    return await self._query_service.get_by_id(query.workflow_id)
```

## Query Service — lokalizacja per agregat

Query Service jest organizowany per agregat. Czyta dane bezposrednio przez SQL/ORM jako read model i grupuje serwisy w folderze `query_services/<nazwa_agregatu>/`:

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
4. **Read model** — Query Service czyta dane i zwraca DTO.
5. **Odpowiedzialnosc aplikacyjna** — Query Handler korzysta z DTO/read model.

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

## Odczyt bez efektow ubocznych

- Handler zapytania NIGDY nie modyfikuje stanu.
- Query Handler korzysta z QueryService i zwraca wynik odczytu.
- Tylko odczyt.

## Stateless

- Handler nie przechowuje stanu między wywołaniami.

> **Reguły nazewnictwa → [naming-convention-standard](../../naming-standards/naming-convention-standard/SKILL.md#queries)**

## Lokalizacja

- Query Handlers: `shell/application/<bc>/query_handlers/`
- Query Services: `shell/application/<bc>/query_services/<nazwa_agregatu>/`
