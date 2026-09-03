---
name: class-and-type-naming-standards
description: Reguły nazewnictwa klas i typów — PascalCase, pełne nazwy biznesowe, wzorce nazw dla wszystkich warstw, reguły dla ID i dziedziczenia.
---

# Class and Type Naming Standards

> Reguły nazewnictwa klas, typów i interfejsów we wszystkich warstwach projektu.

## Podstawowa zasada

**PascalCase** dla wszystkich klas, typów i interfejsów. **Żadnych skrótów** — każda klasa ma pełną, biznesową nazwę.

## Pełne nazwy klas

Jeśli nazwa klasy używa słowa domenowego o wielu znaczeniach (np. "Definition", "Execution",
"Node", "Output"), niesie pełny kwalifikator domenowy; kontekst pakietu pozostaje pomocniczy,
bo klasa działa też poza swoim pakietem.

| SKRÓCONA | PRAWIDŁOWA |
|------------------------|------------|
| `DefinitionProvider` | `GraphDefinitionProvider` |
| `ExecutionChecker` | `SchedulerExecutionChecker` |
| `NodeNavigator` | `NodeExecutionNavigator` |
| `NodeWorkspace` | `NodeExecutionWorkspace` |
| `NodeProcessRunner` | `NodeExecutionProcessRunner` |
| `NodeExecutionPolicy` | `NodeExecutionPolicy` |
| `OutputInterpreter` | `NodeExecutionOutputInterpreter` |
| `FailFastPolicy` | `FailFastNodeExecutionPolicy` |

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
| Child Entity | `PascalCase` | `EnvelopeEvent`, `NodeExecutionResult` |
| Domain Exception | `<AggregateName><ErrorKind>Error` | `GraphExecutionNotFoundError`, `NodeExecutionInvalidStateError`, `NodeExecutionMaxStepExceededError` |

### Domain Exception — szczególne zasady

```
<AggregateName><ErrorKind>Error
```

- `AggregateName` — pełna nazwa agregatu (np. `GraphExecution`, `NodeExecution`, `Workflow`)
- `ErrorKind` — rodzaj błędu w PascalCase (np. `NotFound`, `InvalidState`, `MaxStepExceeded`, `RoleNotResolvable`)
- Sufiks `Error` — obowiązkowy

Przykłady:
| Klasa | Opis |
|-------|------|
| `GraphExecutionNotFoundError` | GraphExecution nie znaleziony |
| `GraphExecutionGraphDefinitionNotFoundError` | GraphDefinition nie znaleziony przez graph_execution |
| `NodeExecutionNotFoundError` | NodeExecution nie znaleziony |
| `NodeExecutionInvalidStateError` | Nieprawidłowy stan NodeExecution |
| `WorkflowInvalidTransitionError` | Nieprawidłowa tranzycja Workflow |
| `NodeExecutionMaxStepExceededError` | Przekroczony max step w NodeExecution |
| `NodeExecutionRoleNotResolvableError` | Rola nierozwiązywalna w NodeExecution |

- NotFound zawsze z sufiksem `Error`
- Invalid state/transition zawsze z sufiksem `Error`
- Wyjątki definiuje się w agregacie którego dotyczą, w katalogu `aggregates/{agregat}/exceptions/`
- Import bezpośrednio z definiującego modułu, nigdy przez re-export warstwę

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
- `NodeStateUpdatedEvent` — techniczne, nie biznesowe

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
- ❌ `NodeStateUpdatedEvent`, `DataSavedEvent`, `ProcessFinishedEvent`

### Klasy aplikacyjne

| Typ | Wzorzec | Przykład |
|-----|---------|----------|
| Command | `<Verb><Object>Command` | `ApproveInvoiceCommand`, `StartWorkflowCommand` |
| Event | `<Aggregate><PastVerb>Event` | `InvoiceApprovedEvent`, `WorkflowStartedEvent` |
| Query | `<Verb><Aggregate>[Projection]Query` | `GetInvoiceByIdQuery`, `GetWorkflowByIdQuery` |
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
| Adapter (cross-BC) | `<Port><Transport>Adapter` | `GraphDefinitionProviderHttpAdapter`, `SessionQueryProviderHttpAdapter` |
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

- Entity: `Entity[TId]` z `shell/platform/domain/base/entity.py`
- Aggregate Root: `AggregateRoot[TId]` z `shell/platform/domain/base/aggregate_root.py`
- Value Object: `ValueObject` z `shell/platform/domain/base/value_object.py`
- Entity ID: `EntityId` z `shell/platform/domain/base/entity_id.py`
- Domain Event: `DomainEvent` z `shell/platform/domain/events/domain_event.py`
- Domain Exception: `DomainError` z `shell/platform/domain/exceptions/domain_error.py`

## Standard nazewnictwa

Szczegółowe reguły nazewnictwa wszystkich artefaktów (handlery, komendy, eventy, query, message, sagi, agenci, deskryptory) znajdują się w osobnym standardzie:
> **[naming-convention-standard](../naming-convention-standard/SKILL.md)**

## Ograniczenia

- Nigdy `@dataclass` dla Entity/Aggregate Root — identity-based equality
- VO zawsze `@dataclass(frozen=True, slots=True)`
- Enum stanów: `StrEnum` dziedziczący po `ValueObject`
- Nazwy klas nie mogą być skrócone — zawsze pełna biznesowa nazwa
