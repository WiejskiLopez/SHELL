---
name: class-and-type-naming-standards
description: Reguły nazewnictwa klas i typów — PascalCase, pełne nazwy biznesowe, wzorce nazw dla wszystkich warstw, reguły dla ID i dziedziczenia.
---

# Class and Type Naming Standards

> Reguły nazewnictwa klas, typów i interfejsów we wszystkich warstwach projektu.

## Podstawowa zasada

**PascalCase** dla wszystkich klas, typów i interfejsów. **Żadnych skrótów** — każda klasa ma pełną, biznesową nazwę.

## Zakaz skróconych nazw klas

Jeśli nazwa klasy używa słowa domenowego, które ma wiele znaczeń w projekcie (np. "Definition", "Execution", "Node", "Output"), musi zawierać pełny kwalifikator domenowy. Nie polegaj na kontekście pakietu — klasa może być używana poza swoim pakietem.

| SKRÓCONA (ZABRONIONA) | PRAWIDŁOWA |
|------------------------|------------|
| `DefinitionProvider` | `GraphExecutionDefinitionProvider` |
| `ExecutionChecker` | `SchedulerExecutionChecker` |
| `NodeNavigator` | `GraphNodeExecutionNavigator` |
| `NodeWorkspace` | `GraphNodeExecutionWorkspace` |
| `NodeProcessRunner` | `GraphNodeExecutionProcessRunner` |
| `NodeExecutionPolicy` | `GraphNodeExecutionPolicy` |
| `OutputInterpreter` | `GraphNodeExecutionOutputInterpreter` |
| `FailFastPolicy` | `FailFastGraphNodeExecutionPolicy` |

## Wzorce nazw według warstwy

### Klasy domenowe

| Typ | Wzorzec | Przykład |
|-----|---------|----------|
| Entity | `PascalCase` | `TaskExecution`, `Session` |
| Aggregate Root | `PascalCase` | `Workflow`, `GraphExecution` |
| Value Object | `PascalCase` | `WorkflowId`, `Status`, `Hash` |
| Domain Event | `PascalCase + Event` | `WorkflowCompletedEvent`, `TaskExecutionCreatedEvent` |
| Domain Service | `PascalCase + Service` | `EnvelopeLifecycleService`, `PricingService` |
| Repository Port | `PascalCase + Repository` | `WorkflowRepository`, `TaskExecutionRepository` |
| Child Entity | `PascalCase` | `EnvelopeEvent`, `GraphNodeExecutionResult` |
| Domain Exception | `PascalCase + domain context` | `WorkflowNotFoundException`, `OrderLimitExceeded` |

### Eventy domenowe — szczególne zasady

```
<AggregateName><PastVerb>Event
```

- `AggregateName` — pełna, biznesowa nazwa agregatu (np. `Workflow`, `GraphExecution`)
- `PastVerb` — czas przeszły dokonany (`Created`, `Started`, `Completed`, `Failed`, `Aborted`, `Opened`, `Closed`, `Looped`)
- Sufiks `Event` — obowiązkowy

✅ **Prawidłowe** (fakt w przeszłości):
- `WorkflowStartedEvent`, `GraphExecutionCompletedEvent`, `TaskExecutionCreatedEvent`
- `OrderPlacedEvent`, `PaymentCompletedEvent`, `StockReservedEvent`

❌ **Nieprawidłowe** (komenda lub niejednoznaczne):
- `PlaceOrderEvent` — to komenda, nie event
- `PaymentEvent` — niejednoznaczne (rozpoczęcie? zakończenie? błąd?)
- `ReserveStockEvent` — to komenda, nie event
- `GraphNodeStateUpdatedEvent` — techniczne, nie biznesowe

### Klasy factory

| Typ | Wzorzec | Przykład |
|-----|---------|----------|
| Factory class | `<Aggregate>Factory` | `GraphExecutionFactory`, `ExecutionFactory` |
| Factory method (rekonstrukcja) | `restore()` | `Execution.restore(id=..., status=...)` |
| Factory method (proste) | `create()` | `Version.initial()`, `Timestamp.now()` |

### Reguła korespondencji handler ↔ komenda/event

Nazwa handlera **koresponduje** z nazwą komendy lub eventu:

| Komenda/Event | Handler |
|---------------|---------|
| `StartWorkflowCommand` | `StartWorkflowHandler` |
| `GraphNodeExecutionCompletedEvent` (główny) | `GraphNodeExecutionCompletedHandler` |
| `GraphNodeExecutionCompletedEvent` (drugorzędny) | `GraphNodeExecutionCompletedPropagateOutputHandler` |

Tylko **jeden** handler (główny) przyjmuje nazwę zgodną z eventem. Pozostałe (drugorzędne) otrzymują kwalifikator biznesowy.

**Zakazany wzorzec:** handler NIGDY nie może mieć prefixu `Handle` — zawsze używa suffixu `Handler`.
- ❌ `HandleGraphExecutionCompleted` — ZABRONIONE
- ✅ `GraphExecutionCompletedEventHandler` — PRAWIDŁOWE
- ❌ `BuildGraphExecutionOnTaskExecutionCreatedEvent` — ZABRONIONE (to handler, nie event)
- ✅ `BuildGraphExecutionOnTaskExecutionCreatedEventHandler` — PRAWIDŁOWE

### Nazwy eventów i komend — biznesowe, nie techniczne

Eventy i komendy opisują **fakty biznesowe** w języku domeny:

- ✅ `WorkflowCompletedEvent`, `TaskExecutionCreatedEvent`, `EnvelopeRoutedEvent`
- ❌ `GraphNodeStateUpdatedEvent`, `DataSavedEvent`, `ProcessFinishedEvent`

### Klasy aplikacyjne

| Typ | Wzorzec | Przykład |
|-----|---------|----------|
| Command | `PascalCase + Command` | `StartWorkflowCommand`, `ImportTaskExecutionCommand` |
| Query | `PascalCase + Query` | `GetWorkflowQuery`, `SearchSimilarQuery` |
| Handler (command) | `<CommandName>Handler` | `StartWorkflowHandler` |
| Handler (event, główny) | `<EventName>Handler` | `GraphNodeExecutionCompletedHandler` |
| Handler (event, drugorzędny) | `<EventName><Qualifier>Handler` | `GraphNodeExecutionCompletedPropagateOutputHandler` |
| Handler (query) | `<QueryName>Handler` | `GetWorkflowHandler` |
| DTO | `PascalCase + Dto` | `GraphDefinitionDto`, `WorkflowDto` |
| Mapper | `PascalCase + Mapper` | `GraphDefinitionMapper`, `PromptMapper` |
| Port (Protocol) | `PascalCase` | `UnitOfWork`, `Clock`, `GraphExecutionDefinitionProvider` |
| Query Service | `PascalCase + QueryService` | `WorkflowQueryService`, `GraphDefinitionQueryService` |
| Strategy | `PascalCase + Strategy` | `AgentStrategy`, `RouterStrategy`, `TaskerStrategy` |

### Klasy infrastrukturalne

| Typ | Wzorzec | Przykład |
|-----|---------|----------|
| SQL Repository | `Sql + PascalCase` | `SqlWorkflowRepository`, `SqlGraphDefinitionRepository` |
| InMemory Repository | `InMemory + PascalCase` | `InMemoryWorkflowRepository` |
| SQL Query Service | `Sql + PascalCase` | `SqlGraphDefinitionQueryService` |
| Adapter | `PascalCase + Adapter` | `GraphExecutionDefinitionProviderAdapter`, `InvoiceAdapter` |
| ORM Model | `PascalCase + Model` | `GraphDefinitionModel`, `TaskExecutionModel` |

## Wzorce dla ID

Każde ID w domenie to osobna klasa Value Object:

```python
class WorkflowId(ValueObject): ...
class TaskExecutionId(ValueObject): ...
class GraphDefinitionId(ValueObject): ...
```

## Dziedziczenie i base klasy

- Entity: `Entity[TId]` z `domain/entities/base/entity.py`
- Aggregate Root: `AggregateRoot[TId]` z `domain/entities/base/aggregate_root.py`
- Value Object: `ValueObject` z `domain/platform/base/value_object.py`
- Domain Event: `DomainEvent` z `domain/platform/events/domain_event.py`
- Domain Exception: `DomainError` z `_base.py`

## Ograniczenia

- Nigdy `@dataclass` dla Entity/Aggregate Root — identity-based equality
- VO zawsze `@dataclass(frozen=True, slots=True)`
- Enum stanów: `StrEnum` dziedziczący po `ValueObject`
- Nazwy klas nie mogą być skrócone — zawsze pełna biznesowa nazwa
