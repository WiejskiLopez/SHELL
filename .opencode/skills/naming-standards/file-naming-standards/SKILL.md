---
name: file-naming-standards
description: Reguły nazewnictwa plików — snake_case, konwersja PascalCase na snake_case, wzorce nazw według typu pliku, pliki testowe.
---

# File Naming Standards

> Reguły nazewnictwa plików `.py` we wszystkich warstwach projektu.

## Podstawowa zasada

Pliki Python używają `snake_case`. Nazwa pliku odpowiada nazwie klasy/portu/interfejsu który zawiera.

```
Klasa:  WorkflowStartHandler
Plik:   workflow_start_handler.py

Klasa:  InvoiceApproveHandler
Plik:   invoice_approve_handler.py

Klasa:  InvoiceApprovedEvent
Plik:   invoice_approved_event.py

Klasa:  InvoiceSummaryDto
Plik:   invoice_summary_dto.py
```

## Konwersja PascalCase → snake_case

Nazwę klasy konwertujesz na nazwę pliku przez wstawienie `_` przed każdą wielką literą (oprócz pierwszej) i zamianę na małe:

```
AaaaBbbbCccc  →  aaaa_bbbb_cccc.py
TaskExecutionId  →  task_execution_id.py
GraphDefinitionDto  →  graph_definition_dto.py
```

## Wzorce nazw plików według typu

| Typ | Wzorzec pliku | Przykład |
|-----|---------------|----------|
| Command | `<verb>_<object>_command.py` | `approve_invoice_command.py` |
| Query | `<aggregate>_<read_op>_query.py` | `invoice_get_by_id_query.py` |
| Message | `<aggregate>_<description>_message.py` | `invoice_summary_message.py` |
| Command Handler | `<aggregate>_<verb>_handler.py` | `invoice_approve_handler.py` |
| Event Handler | `<aggregate>_<past_verb>_handler.py` | `invoice_approved_handler.py` |
| Query Handler | `<aggregate>_<read_op>_handler.py` | `invoice_get_by_id_handler.py` |
| Message Handler | `<aggregate>_<description>_handler.py` | `invoice_summary_handler.py` |
| DTO | `<aggregate>_<projection>_dto.py` | `invoice_summary_dto.py` |
| Domain Event | `<aggregate>_<past_verb>_event.py` | `invoice_approved_event.py` |
| Domain Exception | `<aggregate>_<problem>_exception.py` | `invoice_not_found_exception.py` |
| Entity (child) | `<entity_name>.py` | `envelope_event.py` |
| VO | `<vo_name>.py` | `invoice_id.py` |
| Domain Service | `<aggregate>_<process>_service.py` | `invoice_pricing_service.py` |
| Saga | `<business_process>_saga.py` | `invoice_approval_saga.py` |
| Agent | `<capability>_agent.py` | `approve_invoice_agent.py` |
| Repository Port | `<aggregate>_repository.py` | `invoice_repository.py` |
| SQL Repository | `sql_<aggregate>_repository.py` | `sql_invoice_repository.py` |
| InMemory Repository | `in_memory_<aggregate>_repository.py` | `in_memory_invoice_repository.py` |
| SQL Query Service | `sql_<aggregate>_query_service.py` | `sql_invoice_query_service.py` |
| Adapter | `<adapter_name>.py` | `invoice_adapter.py` |
| ORM Model | `<model_name>.py` | `invoice.py` (zawiera `InvoiceModel`) |
| Strategy | `<strategy_name>.py` | `agent_strategy.py` |
| Port/Protocol | `<port_name>.py` | `unit_of_work.py` |
| Mapper | `<aggregate>_mapper.py` | `invoice_mapper.py` |

### Pliki testowe

```
Plik testu:           test_<nazwa_testowanej_klasy>.py
Funkcja testowa:      test_<opisywana_scenka>()
```

Przykłady:
- `test_execution.py` (zawiera `class TestExecution`)
- `test_create_execution_handler.py`
- `test_sql_execution_repository.py`
- `test_task_execution_name.py`

Katalogi testów odzwierciedlają strukturę warstw:
```
tests/
├── architecture/           # Testy architektury
├── domain/                 # Testy jednostkowe domeny
├── application/            # Testy handlerów
├── infrastructure/         # Testy integracyjne
└── e2e/                    # Testy end-to-end
```

## Pliki specjalne

- `__init__.py` — tylko re-eksport publicznego API pakietu
- Pliki migracji Alembic (`versions/*.py`) — generowane automatycznie

> **Szczegółowe reguły → [naming-convention-standard](../naming-convention-standard/SKILL.md)**

## Ograniczenia

- Jeden plik = jedna główna klasa (wyjątek: małe, ściśle powiązane VO)
- Nazwa pliku musi jednoznacznie identyfikować zawartość
- Brak skrótów w nazwie pliku
