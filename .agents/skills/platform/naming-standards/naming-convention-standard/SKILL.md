---
name: naming-convention-standard
description: Kompletny enterprise standard nazewnictwa dla DDD + CQRS + EDA — Business Capability jako źródło prawdy, wzorce dla wszystkich artefaktów, AI-friendly transformation rules, SemanticDescriptor concept.
---

# Enterprise AI-Native Naming Standard

> Business Capability jest źródłem prawdy dla całej architektury.
> Każdy artefakt reprezentuje tę samą Capability z innej perspektywy.

```
Business Capability: ApproveInvoice
    Aggregate: Invoice
    Verb: Approve
    Result: InvoiceApproved

    ├── invoice.approve()                  # Domain Method
    ├── ApproveInvoiceCommand              # Command
    ├── InvoiceApprovedEvent               # Event
    ├── GetInvoiceByIdQuery                # Query
    ├── InvoiceSummaryMessage              # Message
    ├── ApproveInvoiceHandler              # Command Handler
    ├── InvoiceApprovedHandler             # Event Handler
    ├── GetInvoiceByIdHandler              # Query Handler
    ├── InvoiceSummaryHandler              # Message Handler
    └── InvoiceApprovalSaga                # Saga
```

## 1. Fundamentalna zasada

**Business Capability** definiuje:
- **nazwę** (np. `ApproveInvoice`)
- **agregat** (np. `Invoice`)
- **czasownik** (np. `Approve`)
- **rezultat** (np. `InvoiceApproved`)

Wszystkie artefakty wywodzą się z tej samej Capability.

## 2. Macierz nazewnictwa — wszystkie artefakty

| Artefakt | Wzorzec | Przykład | Pochodzi z |
|----------|---------|----------|------------|
| Domain Method | `snake_case` biznesowa | `invoice.approve()` | Capability |
| Command | `<Verb><Object>Command` | `ApproveInvoiceCommand` | Capability |
| Event | `<Aggregate><PastVerb>Event` | `InvoiceApprovedEvent` | Result |
| Query | `<Verb><Aggregate>[Projection]Query` | `GetInvoiceByIdQuery` | Verb + Aggregate |
| Message | `<Aggregate><Description>Message` | `InvoiceSummaryMessage` | Aggregate + Opis |
| Command Handler | `<Verb><Object>Handler` | `ApproveInvoiceHandler` | Capability |
| Event Handler | `<Aggregate><PastVerb>Handler` | `InvoiceApprovedHandler` | Aggregate + Result |
| Query Handler | `<Verb><Aggregate>Handler` | `GetInvoiceByIdHandler` | Verb + Aggregate |
| Message Handler | `<Aggregate><Description>Handler` | `InvoiceSummaryHandler` | Aggregate + Opis |
| Saga | `<BusinessProcess>Saga` | `InvoiceApprovalSaga` | Business Process |
| Domain Service | `<Aggregate><Process>Service` | `InvoicePricingService` | Aggregate + Process |
| Repository | `<Aggregate>Repository` | `InvoiceRepository` | Aggregate |
| Factory | `<Aggregate>Factory` | `InvoiceFactory` | Aggregate |
| DTO | `<Aggregate><Projection>Dto` | `InvoiceSummaryDto` | Aggregate + Projection |
| Mapper | `<Aggregate>Mapper` | `InvoiceMapper` | Aggregate |
| Entity / Aggregate Root | `<Aggregate>` | `Invoice` | Aggregate |
| Value Object | `<DomainConcept>` | `InvoiceId`, `Money`, `Email` | Domain Concept |
| Exception | `<Aggregate><Problem>Exception` | `InvoiceNotFoundException` | Aggregate + Problem |
| Agent | `<BusinessCapability>Agent` | `ApproveInvoiceAgent` | Capability |

## 3. Domain Methods

Metody domenowe wyrażają **intencję biznesową** — nigdy operację techniczną.

```python
# POPRAWNIE — biznesowa intencja
invoice.approve()
order.reject()
user.assign_role(role)
conversation.start()
task.archive()
document.publish()

# ŹLE — techniczna
invoice.update_status()
order.set_state()
user.execute()
conversation.process()
task.save()
document.set_status()
```

| Prawidłowe | Nieprawidłowe |
|-----------|---------------|
| `approve()` | `update_status()`, `set_state()` |
| `reject()` | `process()`, `execute()` |
| `assign_owner()` | `save()`, `persist()` |
| `start()` | `merge()`, `update()` |
| `archive()` | `handle()`, `run()` |
| `publish()` | `set_status()`, `change_status()` |

## 4. Commands

```
<Verb><Object>Command
```

Command opisuje **intencję wykonania operacji**. Czyta się jak imperatyw.

| Business Capability | Command |
|--------------------|---------|
| ApproveInvoice | `ApproveInvoiceCommand` |
| CreateAccount | `CreateAccountCommand` |
| StartConversation | `StartConversationCommand` |
| AssignOwner | `AssignOwnerCommand` |
| StartWorkflow | `StartWorkflowCommand` |
| RejectInvoice | `RejectInvoiceCommand` |

## 5. Events

```
<Aggregate><PastVerb>Event
```

Event opisuje **fakt biznesowy w przeszłości**.

| Business Result | Event |
|----------------|-------|
| InvoiceApproved | `InvoiceApprovedEvent` |
| InvoiceRejected | `InvoiceRejectedEvent` |
| AccountCreated | `AccountCreatedEvent` |
| ConversationStarted | `ConversationStartedEvent` |
| OwnerAssigned | `OwnerAssignedEvent` |
| WorkflowStarted | `WorkflowStartedEvent` |

Zabronione:
- `ApproveInvoiceEvent` — to komenda, nie event
- `InvoiceEvent` — niejednoznaczne (co się stało?)
- `StatusChangedEvent` — techniczne, nie biznesowe

## 6. Queries

```
<Verb><Aggregate>[Projection]Query
```

Dozwolone operacje: `GetById`, `FindBy*`, `Search`, `List`, `Count`, `Exists`.

| Query | Opis |
|-------|------|
| `GetInvoiceByIdQuery` | Pobierz fakturę po ID |
| `FindInvoiceByNumberQuery` | Znajdź fakturę po numerze |
| `CountInvoicesByStatusQuery` | Policz faktury według statusu |
| `FindUserByEmailQuery` | Znajdź użytkownika po emailu |
| `GetConversationHistoryQuery` | Pobierz historię rozmowy |
| `ListProjectsQuery` | Lista projektów |

## 7. Messages

```
<Aggregate><Description>Message
```

Message opisuje **zawartość** — nigdy akcję.

| Message | Opis |
|---------|------|
| `InvoiceSummaryMessage` | Podsumowanie faktury |
| `ConversationContextMessage` | Kontekst rozmowy |
| `UserProfileMessage` | Profil użytkownika |
| `ExecutionResultMessage` | Wynik wykonania |

## 8. Command Handlers

Handler nazywa się identycznie jak Command — zamieniając sufiks `Command` na `Handler`.

```
<Verb><Object>Handler
```

**Reguła:** `{Command}Command` → `{Command}Handler`. Proste podstawienie — żadnej deduplikacji.

| Command | Handler |
|---------|---------|
| `ApproveInvoiceCommand` | `ApproveInvoiceHandler` |
| `StartWorkflowCommand` | `StartWorkflowHandler` |
| `CreateAccountCommand` | `CreateAccountHandler` |
| `AssignOwnerCommand` | `AssignOwnerHandler` |
| `OpenSessionCommand` | `OpenSessionHandler` |
| `RejectInvoiceCommand` | `RejectInvoiceHandler` |

## 9. Event Handlers

```
<Aggregate><PastVerb>Handler
```

| Event | Handler |
|-------|---------|
| `InvoiceApprovedEvent` | `InvoiceApprovedHandler` |
| `InvoiceRejectedEvent` | `InvoiceRejectedHandler` |
| `AccountCreatedEvent` | `AccountCreatedHandler` |
| `ConversationStartedEvent` | `ConversationStartedHandler` |
| `WorkflowStartedEvent` | `WorkflowStartedHandler` |
| `WorkflowCompletedEvent` | `WorkflowCompletedHandler` |

## 10. Query Handlers

Handler nazywa się identycznie jak Query — zamieniając sufiks `Query` na `Handler`.

```
<Verb><Aggregate>Handler
```

**Reguła:** `{Query}Query` → `{Query}Handler`. Proste podstawienie.

| Query | Handler |
|-------|---------|
| `GetInvoiceByIdQuery` | `GetInvoiceByIdHandler` |
| `FindInvoiceByNumberQuery` | `FindInvoiceByNumberHandler` |
| `FindUserByEmailQuery` | `FindUserByEmailHandler` |
| `GetConversationHistoryQuery` | `GetConversationHistoryHandler` |

## 11. Message Handlers

```
<Aggregate><Description>Handler
```

| Message | Handler |
|---------|---------|
| `InvoiceSummaryMessage` | `InvoiceSummaryHandler` |
| `ConversationContextMessage` | `ConversationContextHandler` |

## 12. Sagas

```
<BusinessProcess>Saga
```

Saga opisuje **proces biznesowy**, nie agregat.

| Saga | Proces |
|------|--------|
| `InvoiceApprovalSaga` | Zatwierdzanie → notyfikacja → archiwizacja |
| `UserRegistrationSaga` | Rejestracja → weryfikacja → welcome email |
| `OrderFulfillmentSaga` | Payment → pack → ship |
| `WorkflowExecutionSaga` | Execution lifecycle |

Saga orkiestruje komendy. Nigdy nie implementuje logiki domenowej.

## 13. Domain Services

```
<Aggregate><Process>Service
```

| Service | Odpowiedzialność |
|---------|-----------------|
| `InvoicePricingService` | Kalkulacja cen faktury |
| `OrderFraudDetectionService` | Wykrywanie fraudów zamówień |
| `UserValidationService` | Walidacja użytkownika |
| `ConversationScoringService` | Scoring konwersacji |

## 14. Pozostałe artefakty

| Artefakt | Wzorzec | Przykład |
|----------|---------|----------|
| Entity / Aggregate Root | `<Aggregate>` | `Invoice`, `User`, `Workflow` |
| Value Object | `<DomainConcept>` | `InvoiceId`, `Money`, `Email`, `Status` |
| Repository | `<Aggregate>Repository` | `InvoiceRepository` |
| Factory | `<Aggregate>Factory` | `InvoiceFactory` |
| DTO | `<Aggregate><Projection>Dto` | `InvoiceSummaryDto` |
| Mapper | `<Aggregate>Mapper` | `InvoiceMapper` |
| Exception | `<Aggregate><Problem>Exception` | `InvoiceNotFoundException` |
| Agent | `<BusinessCapability>Agent` | `ApproveInvoiceAgent` |

## 15. AI transformation rules

### Reguła #1: Command → Handler
```
ApproveInvoiceCommand
    → zamień sufiks Command → Handler
    → ApproveInvoiceHandler
```

### Reguła #2: Event → Handler
```
InvoiceApprovedEvent
    → zamień sufiks Event → Handler
    → InvoiceApprovedHandler
```

### Reguła #3: Query → Handler
```
GetInvoiceByIdQuery
    → zamień sufiks Query → Handler
    → GetInvoiceByIdHandler
```

### Reguła #4: Message → Handler
```
InvoiceSummaryMessage
    → zamień sufiks Message → Handler
    → InvoiceSummaryHandler
```

### Reguła #5: PascalCase → snake_case (nazwa pliku)
```
ApproveInvoiceHandler  →  approve_invoice_handler.py
InvoiceApprovedEvent   →  invoice_approved_event.py
GetInvoiceByIdQuery    →  get_invoice_by_id_query.py
```

## 16. SemanticDescriptor (koncept)

Deskryptor semantyczny — to on jest embeddowany do vector search, nie nazwa klasy.

```python
@dataclass(frozen=True)
class SemanticDescriptor:
    domain: str                    # "Billing"
    bounded_context: str           # "InvoiceManagement"
    aggregate: str                 # "Invoice"
    capability: str                # "ApproveInvoice"
    artifact_type: str             # "Command" | "Event" | "Query" | "Handler" | ...
    description: str               # "Approves invoice after business validation"
    keywords: list[str]            # ["invoice", "approval", "billing"]
```

Nazwa klasy determinuje 4 z 7 pól:
```
ApproveInvoiceHandler → aggregate=Invoice, capability=ApproveInvoice, artifact_type=Handler
GetInvoiceByIdHandler → aggregate=Invoice, capability=GetInvoiceById, artifact_type=Handler
```

## 17. Struktura projektu

```
<domain|application|infrastructure>/<bounded_context>/
    commands/<aggregate>/
        <verb>_<object>_command.py
    command_handlers/<aggregate>/
        <verb>_<object>_handler.py
    events/<aggregate>/
        <aggregate>_<past_verb>_event.py
    event_handlers/<aggregate>/
        <aggregate>_<past_verb>_handler.py
    queries/<aggregate>/
        <verb>_<aggregate>_query.py
    query_handlers/<aggregate>/
        <verb>_<aggregate>_handler.py
    messages/<aggregate>/
        <aggregate>_<description>_message.py
    message_handlers/<aggregate>/
        <aggregate>_<description>_handler.py
    sagas/<aggregate>/
        <business_process>_saga.py
    services/<aggregate>/
        <aggregate>_<process>_service.py
    dto/<aggregate>/
        <aggregate>_<projection>_dto.py
    mappers/<aggregate>/
        <aggregate>_mapper.py
```

Przykład dla BC `billing`:
```
application/billing/
    commands/invoice/
        approve_invoice_command.py
    command_handlers/invoice/
        approve_invoice_handler.py
    events/invoice/
        invoice_approved_event.py
    event_handlers/invoice/
        invoice_approved_handler.py
    queries/invoice/
        get_invoice_by_id_query.py
    query_handlers/invoice/
        get_invoice_by_id_handler.py
    messages/invoice/
        invoice_summary_message.py
    sagas/invoice/
        invoice_approval_saga.py
    dto/invoice/
        invoice_summary_dto.py
    mappers/invoice/
        invoice_mapper.py

domain/billing/
    aggregates/invoice/
        invoice.py
        events/
            invoice_approved_event.py
        value_objects/
            invoice_id.py
            invoice_status.py
            money.py
    services/invoice/
        invoice_pricing_service.py
    repositories/invoice/
        invoice_repository.py
```

## 18. Przepływ end-to-end

```
invoice.approve()
    │
    ├── Publishes: ApproveInvoiceCommand
    │       │
    │       ▼
    ├── ApproveInvoiceHandler.handle(approve_invoice_command)
    │       │
    │       ▼
    ├── Invoice.approve()                     # guard → mutate → event
    │       │
    │       ▼
    ├── InvoiceApprovedEvent
    │       │
    │       ├── InvoiceApprovedHandler.handle(invoice_approved_event)
    │       │       │
    │       │       ▼
    │       │   Publish to outbox
    │       │
    │       └── InvoiceApprovalSaga.on_invoice_approved()
    │               │
    │               ├── Publishes: NotifyCustomerCommand
    │               ├── Publishes: ArchiveInvoiceCommand
    │               └── Publishes: UpdateLedgerCommand
```

## 19. Zakazane wzorce

| Wzorzec | Problem | Poprawny |
|---------|---------|----------|
| `InvoiceApproveInvoiceHandler` | Redundancja agregatu | `ApproveInvoiceHandler` |
| `InvoiceInvoiceApprovedHandler` | Redundancja agregatu | `InvoiceApprovedHandler` |
| `HandleInvoiceApprove` | Zły prefix | `ApproveInvoiceHandler` |
| `ApproveInvoiceEventHandler` | Event w nazwie handlera | `InvoiceApprovedHandler` |
| `InvoiceApproveHandler` | Aggregate-first (stara konwencja) | `ApproveInvoiceHandler` |
| `InvoiceGetByIdHandler` | Aggregate-first (stara konwencja) | `GetInvoiceByIdHandler` |
| `CommandHandler` (base) | Generyczna nazwa | Konkretna: `ApproveInvoiceHandler` |
| `NodeStateUpdatedEvent` | Techniczne, nie biznesowe | `NodeStateChangedEvent` |
