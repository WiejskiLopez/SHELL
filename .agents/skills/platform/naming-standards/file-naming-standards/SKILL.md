# File Naming Standards

> Reguły nazewnictwa plików `.py` we wszystkich warstwach projektu.

## Podstawowa zasada

Pliki Python używają `snake_case`. Nazwa pliku odpowiada nazwie klasy/portu/interfejsu który zawiera.

```
Klasa:  StartWorkflowHandler
Plik:   start_workflow_handler.py

Klasa:  GraphDefinitionDto
Plik:   graph_definition_dto.py

Klasa:  WorkflowCompletedEvent
Plik:   workflow_completed_event.py
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
| Command | `<command_name>.py` | `start_workflow_command.py` |
| Query | `<query_name>.py` | `get_workflow_query.py` |
| Handler (command) | `<command_name>_handler.py` | `start_workflow_handler.py` |
| Handler (query) | `<query_name>_handler.py` | `get_workflow_handler.py` |
| Handler (event, main) | `<event_name>_handler.py` | `graph_node_execution_completed_handler.py` |
| Handler (event, secondary) | `<event_name>_<qualifier>_handler.py` | `graph_node_execution_completed_propagate_output_handler.py` |
| DTO | `<dto_name>.py` | `graph_definition_dto.py` |
| Domain Event | `<aggregate_name>_<past_verb>_event.py` | `workflow_started_event.py` |
| Domain Exception | `<exception_name>.py` | `workflow_not_found_exception.py` |
| Entity (child) | `<entity_name>.py` | `envelope_event.py` |
| VO | `<vo_name>.py` | `task_execution_id.py` |
| Domain Service | `<service_name>.py` | `execution_creation_service.py` |
| Repository Port | `<repo_name>.py` | `workflow_repository.py` |
| SQL Repository | `sql_<repo_name>.py` | `sql_workflow_repository.py` |
| InMemory Repository | `in_memory_<repo_name>.py` | `in_memory_workflow_repository.py` |
| SQL Query Service | `sql_<service_name>.py` | `sql_graph_definition_query_service.py` |
| Adapter | `<adapter_name>.py` | `graph_execution_definition_provider_adapter.py` |
| ORM Model | `<model_name>.py` (sufiks `_model` pomijany) | `graph_definition.py` (zawiera `GraphDefinitionModel`) |
| Strategy | `<strategy_name>.py` | `agent_strategy.py` |
| Port/Protocol | `<port_name>.py` | `unit_of_work.py` |
| Mapper | `<mapper_name>.py` | `graph_definition_mapper.py` |

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

## Ograniczenia

- Jeden plik = jedna główna klasa (wyjątek: małe, ściśle powiązane VO)
- Nazwa pliku musi jednoznacznie identyfikować zawartość
- Brak skrótów w nazwie pliku
