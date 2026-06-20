# Kontrakty między domenowe — DTO, porty i Anti-Corruption Layer

> Reguły komunikacji między domenami (bounded context). Każda domena jest potencjalnie osobnym serwisem w przyszłości — kontrakty muszą być stabilne i niezależne.

## DTO należy do domeny źródłowej

DTO (kontrakt danych) jest własnością **domeny która go definiuje** (źródłowej). Domena docelowa może go używać, ale nigdy nie modyfikuje ani nie przejmuje na własność.

```
Definition Domain (źródło)                Execution Domain (docelowa)
┌────────────────────────┐                ┌──────────────────────────┐
│ GraphDefinitionDto     │── TYPE_CHECKING│ GraphExecutionDefinitionProvider        │
│ GraphNodeDefinitionDto │  (tylko typy)  │ (port/Protocol)          │
│ (application/dto/)     │                │ (domain/ports/)          │
└────────────────────────┘                └──────────────────────────┘
```

### Gdzie umieszczać DTO?

- **DTO definiowane przez domenę źródłową** → `shell/application/<domena>/dto/nazwa_dto.py`
- Są to dataclasses w warstwie aplikacyjnej domeny źródłowej
- Reprezentują kontrakt API / read model tej domeny

### Gdzie umieszczać port?

- **Port w domenie docelowej** → `shell/domain/<domena>/ports/nazwa_portu.py`
- Port (Protocol) definiuje interfejs potrzebny domenie docelowej
- W sygnaturach portu można używać DTO z domeny źródłowej — pod `TYPE_CHECKING` (typy są tylko dla type-checkera, z `from __future__ import annotations` nie są importowane w runtime)

```python
# shell/domain/execution/ports/graph_execution_definition_provider.py
from __future__ import annotations
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.application.definition.dto.graph_definition import GraphDefinitionDto

class GraphExecutionDefinitionProvider(Protocol):
    async def get_graph_definition(self, definition_id: str) -> GraphDefinitionDto | None: ...
```

## Każda domena ma własne DTO — z mapowaniem w adapterze

Domena docelowa definiuje **swoje własne DTO** (value objects) reprezentujące dane których potrzebuje. Adapter w infrastrukturze mapuje między DTO źródłowej domeny a DTO docelowej.

```
Definition Domain (źródło)       Infrastructure                   Execution Domain (docelowa)
┌──────────────────────┐        ┌──────────────────────┐         ┌──────────────────────────┐
│ GraphDefinitionDto   │───────→│ GraphExecutionDefinitionProviderAdapter   │────────→│ GraphExecutionDefinitionProvider       │
│ (application/dto/)   │        │ Adapter              │         │ (port — zwraca własne)   │
└──────────────────────┘        │ mapuje:              │         └──────────────────────────┘
                                │ src DTO → exec DTO   │                   │
                                └──────────────────────┘                   ▼
                                                                 ┌──────────────────────────┐
                                                                 │ GraphExecutionDefinition  │
                                                                 │ GraphNodeExecutionDef     │
                                                                 │ (domain/value_objects/)   │
                                                                 └──────────────────────────┘
```

### Dlaczego?

1. **Decoupling** — domena docelowa nie zależy od struktury DTO źródła. Gdy źródło zmieni swój DTO, zmienia się tylko adapter (mapowanie), nie cała logika docelowa.
2. **Odporność na zmiany** — w przyszłości źródło może stać się serwisem REST/gRPC. Jego DTO może się różnić od obecnego. Adapter jest jedynym miejscem które trzeba zmienić.
3. **Kontekst domeny** — to samo pojęcie może mieć różne znaczenie w różnych domenach. Własny DTO pozwala nazwać pola językiem domeny docelowej.

### Zasady

1. Domena źródłowa definiuje `GraphDefinitionDto` w `application/<domena>/dto/` — to jest kontrakt API
2. Domena docelowa definiuje `GraphExecutionDefinition` w `domain/<domena>/value_objects/` — to jest wewnętrzny model
3. Adapter w `infrastructure/<domena_docelowa>/` mapuje źródłowy DTO → docelowy DTO
4. Port w domenie docelowej operuje na **swoim własnym DTO**

## Adapter używa serwisów kwerend (read model), nie repozytoriów domenowych

Adapter który realizuje operację odczytu (pobranie danych z innej domeny) **nie może wołać repozytoriów domenowych** (`uow.<domena>.get_by_id()`). Zamiast tego:

1. Domena źródłowa definiuje serwis kwerend (QueryService Protocol) w `application/<domena>/ports/queries/`
2. Infrastruktura implementuje go jako SQL query service w `infrastructure/<domena>/persistence/sql/services/` — mapuje ORM modele → DTO bez encji domenowych
3. Adapter wstrzykuje QueryService (przez DI) i go woła

```
Adapter w docelowej infrastrukturze
         │
         ▼
GraphDefinitionQueryService (port odczytu z definition domain)
         │
         ▼
SqlGraphDefinitionQueryService (infrastructure/definition)
         │
         ▼
SQLAlchemy model → DTO (bez encji domenowych!)
```

### Dlaczego?

1. **CQRS** — odczyty nie powinny przechodzić przez domenowe encje (agregaty)
2. **Performance** — query services mogą robić optymalne zapytania SQL (JOINy, projekcje), bez ładowania całych agregatów
3. **Separacja** — zmiana w read modelu nie wpływa na domenę (encje, reguły biznesowe)

### Przykład

```python
# shell/infrastructure/execution/graph_execution_definition_provider_adapter.py
class GraphExecutionDefinitionProviderAdapter(GraphExecutionDefinitionProvider):
    def __init__(self, query_service: GraphDefinitionQueryService) -> None:
        self._query_service = query_service  # ← port odczytu z definition

    async def get_graph_definition(self, definition_id: str) -> GraphExecutionDefinition | None:
        source_dto = await self._query_service.get_graph_definition(definition_id)
        if source_dto is None:
            return None
        return self._map_to_execution(source_dto)  # ← mapowanie DTO

    def _map_to_execution(self, source: GraphDefinitionDto) -> GraphExecutionDefinition:
        return GraphExecutionDefinition(
            id=source.id,
            name=source.name,
            ...
        )
```

## Komunikacja asynchroniczna — eventy między domenami przez porty

Gdy handler w domenie A subskrybuje event z domeny B, **nie importuje bezpośrednio typu eventu z domeny B**. Zamiast tego:

1. Domena A definiuje port (Protocol) dla zdarzenia które chce obsłużyć
2. Handler w domenie A implementuje ten port
3. Adapter w infrastrukturze subskrybuje event z domeny B, konwertuje go i woła port domeny A

```
Execution Domain event (WorkflowCompletedEvent)
         │
         ▼
ExecutionWorkflowOutcomeAdapter (infrastructure/scheduling)
         │   konwertuje event → proste parametry
         ▼
WorkflowOutcomeReceiver (port w scheduling domain)
         │
         ▼
SchedulerExecutionHandler (implementuje port)
```

### Przykład

```python
# shell/domain/scheduling/ports/workflow_outcome_receiver.py
class WorkflowOutcomeReceiver(Protocol):
    async def on_workflow_completed(self, workflow_id: str) -> None: ...
    async def on_workflow_failed(self, workflow_id: str, error: str) -> None: ...

# shell/infrastructure/scheduling/execution_workflow_outcome_adapter.py
class ExecutionWorkflowOutcomeAdapter:
    def __init__(self, receiver: WorkflowOutcomeReceiver) -> None:
        self._receiver = receiver

    async def handle(self, event: Union[WorkflowCompletedEvent, WorkflowFailedEvent]) -> None:
        if isinstance(event, WorkflowCompletedEvent):
            await self._receiver.on_workflow_completed(event.workflow_id.value)
        elif isinstance(event, WorkflowFailedEvent):
            await self._receiver.on_workflow_failed(event.workflow_id.value, event.error or "")
```

## Podsumowanie — schemat komunikacji między domenowej

| Typ komunikacji | Port w | Adapter w | Uwagi |
|----------------|--------|-----------|-------|
| Odczyt danych (sync) | domena docelowa (domain/ports/) | infrastructure/<domena_docelowa>/ | Używa QueryService (read model), nie domain repo |
| Event (async) | domena subskrybująca (domain/ports/) | infrastructure/<domena_subskrybująca>/ | Konwertuje event źródłowy na wywołanie portu |
| DTO | domena źródłowa (application/dto/) | — | Źródło definiuje kontrakt, docelowa mapuje na własne VO |
