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

> **Reguły nazewnictwa handlerów, komend, eventów, query, message → patrz [naming-convention-standard](../naming-convention-standard/SKILL.md#handlers)**
>
> Ten skill zawiera tylko ogólne reguły PascalCase i zakaz skrótów. Szczegółowe wzorce nazewnictwa wszystkich artefaktów są w dedykowanym standardzie.

### Nazwy eventów i komend — biznesowe, nie techniczne

Eventy i komendy opisują **fakty biznesowe** w języku domeny:

- ✅ `WorkflowCompletedEvent`, `TaskExecutionCreatedEvent`, `EnvelopeRoutedEvent`
- ❌ `GraphNodeStateUpdatedEvent`, `DataSavedEvent`, `ProcessFinishedEvent`

### Klasy aplikacyjne

| Typ | Wzorzec | Przykład |
|-----|---------|----------|
| Command | `<Verb><Object>Command` | `ApproveInvoiceCommand`, `StartWorkflowCommand` |
| Event | `<Aggregate><PastVerb>Event` | `InvoiceApprovedEvent`, `WorkflowStartedEvent` |
| Query | `<Aggregate><ReadOp>[Projection]Query` | `InvoiceGetByIdQuery`, `WorkflowGetByIdQuery` |
| Message | `<Aggregate><Description>Message` | `InvoiceSummaryMessage` |
| DTO | `<Aggregate><Projection>Dto` | `InvoiceSummaryDto`, `WorkflowDto` |
| Mapper | `<Aggregate>Mapper` | `InvoiceMapper`, `WorkflowMapper` |
| Port (Protocol) | `PascalCase` | `UnitOfWork`, `Clock`, `InvoiceRepository` |
| Query Service | `<Aggregate>QueryService` | `InvoiceQueryService` |
| Strategy | `PascalCase + Strategy` | `AgentStrategy`, `RouterStrategy` |
| Saga | `<BusinessProcess>Saga` | `InvoiceApprovalSaga` |
| Agent | `<BusinessCapability>Agent` | `ApproveInvoiceAgent` |

### Klasy infrastrukturalne

| Typ | Wzorzec | Przykład |
|-----|---------|----------|
| SQL Repository | `Sql + PascalCase` | `SqlWorkflowRepository`, `SqlGraphDefinitionRepository` |
| InMemory Repository | `InMemory + PascalCase` | `InMemoryWorkflowRepository` |
| SQL Query Service | `Sql + PascalCase` | `SqlGraphDefinitionQueryService` |
| Adapter | `PascalCase + Adapter` | `GraphExecutionDefinitionProviderAdapter`, `InvoiceAdapter` |
| ORM Model | `PascalCase + Model` | `GraphDefinitionModel`, `TaskExecutionModel` |

## Wzorce dla ID

Każde ID w domenie dziedziczy po `EntityId`:

```python
class WorkflowId(EntityId): ...
class TaskExecutionId(EntityId): ...
class GraphDefinitionId(EntityId): ...
```

### Cross-BC Reference IDs (IdRef pattern)

Gdy agregat w BC A potrzebuje referencji do agregatu z BC B,
używamy sufiksu `IdRef`:

```python
class GraphDefinitionIdRef(EntityId): ...   # execution BC → definition BC
class UserIdRef(EntityId): ...              # session BC → user BC
class ProjectIdRef(EntityId): ...           # session BC → projekt BC
class SessionIdRef(EntityId): ...           # execution BC → session BC
```

Zasady:
- **BC-właściciel**: `{AggregateName}Id` (np. `GraphDefinitionId`)
- **BC-referencjonujący**: `{AggregateName}IdRef` (np. `GraphDefinitionIdRef`)
- `IdRef` = Reference — oznacza że to identyfikator encji z innego BC
- Każdy BC definiuje własne `IdRef` dla obcych agregatów — celowa duplikacja dla izolacji
- Nigdy nie importuj `Id` z innego BC — zawsze używaj własnego `IdRef`

## Dziedziczenie i base klasy

- Entity: `Entity[TId]` z `shell/domain/platform/base/entity.py`
- Aggregate Root: `AggregateRoot[TId]` z `shell/domain/platform/base/aggregate_root.py`
- Value Object: `ValueObject` z `shell/domain/platform/base/value_object.py`
- Entity ID: `EntityId` z `shell/domain/platform/base/entity_id.py`
- Domain Event: `DomainEvent` z `shell/domain/platform/events/domain_event.py`
- Domain Exception: `DomainError` z `_base.py`

## Standard nazewnictwa

Szczegółowe reguły nazewnictwa wszystkich artefaktów (handlery, komendy, eventy, query, message, sagi, agenci, deskryptory) znajdują się w osobnym standardzie:
> **[naming-convention-standard](../naming-convention-standard/SKILL.md)**

## Ograniczenia

- Nigdy `@dataclass` dla Entity/Aggregate Root — identity-based equality
- VO zawsze `@dataclass(frozen=True, slots=True)`
- Enum stanów: `StrEnum` dziedziczący po `ValueObject`
- Nazwy klas nie mogą być skrócone — zawsze pełna biznesowa nazwa
