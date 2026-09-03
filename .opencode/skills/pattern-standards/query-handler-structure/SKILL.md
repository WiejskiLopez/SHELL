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

- Pojedyncza `async handle(self, query: <QueryName>) -> <QueryDto> | list[<QueryDto>] | None`.
- Zwraca DTO/read model nalezacy do warstwy aplikacji.

```python
async def handle(self, query: WorkflowGetByIdQuery) -> WorkflowDto | None:
    return await self._query_service.get_by_id(query.workflow_id)
```

## Query Service — lokalizacja per agregat

Query Service (port odczytu, Protocol) jest organizowany **per agregat** i leży obok innych aplikacyjnych portów:

```
shell/<service>/application/<bc>/<aggregate>/ports/<aggregate>_query_service.py
```

Implementacja SQL siedzi w infrastrukturze agregatu:

```
shell/<service>/infrastructure/<bc>/<aggregate>/persistence/sql/services/<aggregate>_query_service.py
```

### Zasady

1. **Per agregat, nie per BC** — query service jest grupowany po agregacie; port w `ports/`, implementacja w persistence.
2. **Łatwa ekstrakcja** — jeśli agregat zostanie wydzielony do osobnego mikroserwisu, port + handler + implementacja są przenoszone razem.
3. **Port (Protocol) używany w query handlerze** — handler wstrzykuje port, framework nie sięga po query service bezpośrednio (testy `test_cqrs_query_discipline`).
4. **Read model** — Query Service czyta dane i zwraca DTO.
5. **Jeden serwis = grupa powiązanych zapytań** — port może mieć wiele metod (list, detail, history), ale wszystkie dotyczą tego samego read modelu / agregatu.

```python
# shell/<service>/application/<bc>/<aggregate>/ports/<aggregate>_query_service.py
class WorkflowQueryService(Protocol):
    async def get_active(self) -> list[WorkflowSummaryDto]: ...
    async def get_by_owner(self, owner_id: UserId) -> list[WorkflowSummaryDto]: ...
```

## Odczyt bez efektow ubocznych

- Handler zapytania NIGDY nie modyfikuje stanu.
- Query Handler korzysta z QueryService i zwraca wynik odczytu.
- Tylko odczyt.

## Stateless

- Handler nie przechowuje stanu między wywołaniami.

> **Reguły nazewnictwa → [naming-convention-standard](../../naming-standards/naming-convention-standard/SKILL.md#queries)**

## Lokalizacja

- Query Handlers: `shell/<service>/application/<bc>/<aggregate>/query_handlers/`
- Query Service (port): `shell/<service>/application/<bc>/<aggregate>/ports/<aggregate>_query_service.py`
- Implementacja SQL: `shell/<service>/infrastructure/<bc>/<aggregate>/persistence/sql/services/`
