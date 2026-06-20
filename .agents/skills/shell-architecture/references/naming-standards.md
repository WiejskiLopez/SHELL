# Standardy nazewnictwa — reguły dla całej aplikacji

> Standardy dotyczą wszystkich warstw: `domain/`, `application/`, `infrastructure/`, `framework/`, `bootstrap/`, `shared/`.

## Zakaz skróconych nazw zmiennych

**Nigdy nie skracaj nazw zmiennych.** Każda zmienna musi mieć pełną, biznesową nazwę która oddaje jej znaczenie w języku domeny.

Skracanie nazw zmiennych jest zabronione, ponieważ:
1. Zaciera intencję biznesową kodu
2. Wymusza domyślanie się znaczenia przez czytającego
3. Tworzy niespójność — ta sama nazwa w różnych miejscach może oznaczać różne rzeczy
4. Utrudnia refaktoryzację i wyszukiwanie

### ❌ Przykłady ZABRONIONE (skrócone nazwy)

| Skrócona nazwa | Problem |
|----------------|---------|
| `wf_id` | Nie wiadomo czy `workflow_id` czy `workflow_instance_id` |
| `env_id` | Czy `envelope_id` czy `environment_id`? |
| `parent_id` | Czy `parent_graph_execution_id` czy `parent_workflow_id`? |
| `msg_id` | `message_id` to pełna nazwa |
| `gd` | `graph_definition` to pełna nazwa |
| `nd` / `node_dto` | `graph_node_definition` — sufiks `dto` jest mylący gdy to nie jest DTO |
| `dto` | Zawsze opisz co to za DTO: `graph_definition_dto` |
| `def_id` | `definition_id` lub `graph_definition_id` |
| `cmd` | `command` (chyba że to lista argumentów CLI, wtedy `command_line`) |
| `ctx` | `context` — ale lepiej opisać: `sub_graph_context`, `application_context` |
| `args` | `arguments` — ale lepiej opisać: `type_arguments`, `log_arguments` |
| `wf` | `workflow` |
| `stmt` (poza infrastructure) | W warstwie domenowej/aplikacyjnej to skrót od `statement` — nie biznesowe |
| `res` / `ret` | `result` (a jeszcze lepiej: `execution_result`, `query_result`) |

### ✅ Przykłady PRAWIDŁOWE

```python
# ZAMIAST:
wf_id = WorkflowId(cmd.workflow_id)

# PISZ:
workflow_id = WorkflowId(cmd.workflow_id)

# ZAMIAST:
parent_id = graph_execution.parent_graph_execution_id

# PISZ:
parent_graph_execution_id = graph_execution.parent_graph_execution_id

# ZAMIAST:
gd = await self._definition_provider.get_graph_definition(def_id)

# PISZ:
graph_definition = await self._definition_provider.get_graph_definition(definition_id)

# ZAMIAST:
for node_dto in graph_definition.graph_node_execution_definitions:

# PISZ:
for graph_node_definition in graph_definition.graph_node_execution_definitions:
```

### Wyjątki (dozwolone)

| Wyjątek | Kiedy dozwolony | Przykład |
|---------|----------------|----------|
| `e` | `except Exception as e` | Tylko w klauzuli `except` |
| `index` | Pętle czysto matematyczne | `for index in range(count)` — tylko gdy zmienna NIE reprezentuje konceptu biznesowego |
| `_` | Throwaway | Standard Python dla nieużywanych wartości |
| `self`, `cls` | Metody klas | Słowa kluczowe Python |
| `session` | Infrastructure persistence | ORM standard |
| `stmt` | Infrastructure persistence | ORM standard (SQLAlchemy) |
| `conn` | Infrastructure persistence | Połączenie z bazą danych |
| `engine` | Infrastructure persistence | Silnik SQLAlchemy |

**Uwaga:** Jeśli pętla iteruje po kolekcji biznesowej (np. lista węzłów, lista zadań), zmienna pętli **musi** mieć pełną nazwę biznesową — `for graph_node_definition in graph_node_definitions:`, nie `for nd in nodes:`.

## Nazewnictwo klas

### Klasy domenowe

| Typ | Wzorzec | Przykład |
|-----|---------|----------|
| Entity | `PascalCase` | `TaskExecution`, `Session` |
| Aggregate Root | `PascalCase` | `Workflow`, `GraphExecution` |
| Value Object | `PascalCase` | `WorkflowId`, `Status`, `Hash` |
| Domain Event | `PascalCase + Event` | `WorkflowCompletedEvent`, `TaskExecutionCreatedEvent` |
| Domain Service | `PascalCase + Service` | `EnvelopeLifecycleService`, `GraphNodeExecutionNavigator` |
| Repository Port | `PascalCase + Repository` | `WorkflowRepository`, `TaskExecutionRepository` |

### Klasy aplikacyjne

| Typ | Wzorzec | Przykład |
|-----|---------|----------|
| Command | `PascalCase + Command` | `StartWorkflowCommand`, `ImportTaskExecutionCommand` |
| Query | `PascalCase + Query` | `GetWorkflowQuery`, `SearchSimilarQuery` |
| Handler (command) | `PascalCase + Handler` (taka sama nazwa jak Command) | `StartWorkflowCommand` → `StartWorkflowHandler` |
| Handler (event, główny) | `PascalCase + Handler` (taka sama nazwa jak Event) | `GraphNodeExecutionCompletedEvent` → `GraphNodeExecutionCompletedHandler` |
| Handler (event, drugorzędny) | `PascalCase + kwalifikator + Handler` | `SpawnSubGraphsOnPlannerCompletionHandler` |
| DTO | `PascalCase + Dto` | `GraphDefinitionDto`, `WorkflowDto` |
| Mapper | `PascalCase + Mapper` | `GraphDefinitionMapper`, `PromptMapper` |
| Port (Protocol) | `PascalCase` | `UnitOfWork`, `Clock`, `DefinitionProvider` |
| Query Service | `PascalCase + QueryService` | `WorkflowQueryService`, `GraphDefinitionQueryService` |

### Klasy infrastrukturalne

| Typ | Wzorzec | Przykład |
|-----|---------|----------|
| SQL Repository | `Sql + PascalCase` | `SqlWorkflowRepository`, `SqlGraphDefinitionRepository` |
| InMemory Repository | `InMemory + PascalCase` | `InMemoryWorkflowRepository` |
| SQL Query Service | `Sql + PascalCase` | `SqlGraphDefinitionQueryService` |
| Adapter | `PascalCase + Adapter` | `DefinitionProviderAdapter`, `ExecutionWorkflowOutcomeAdapter` |
| ORM Model | `PascalCase + Model` | `GraphDefinitionModel`, `TaskExecutionModel` |

## Nazewnictwo plików

- Pliki Python: `snake_case` z nazwą odpowiadającą klasie
- Plik z klasą `StartWorkflowHandler` → `start_workflow_handler.py`
- Plik z klasą `GraphDefinitionDto` → `graph_definition_dto.py`
- Plik z klasą `SqlWorkflowRepository` → `sql_workflow_repository.py`
- Plik z modelem `GraphDefinitionModel` → `graph_definition.py` (sufiks `_model` pomijamy w nazwie pliku)

## Nazewnictwo metod na agregatach

Metody na agregatach muszą wyrażać **intencję biznesową**, nie operację techniczną:

- ✅ `order.confirm()`, `workflow.mark_completed()`, `task.assign_to(user)`, `invoice.cancel()`
- ❌ `order.save()`, `workflow.update()`, `task.merge()`, `invoice.set_status()`, `aggregate.persist()`

## Porządek składowych w klasie

Składowe klasy muszą być uporządkowane: **najpierw publiczne, potem prywatne**. Prywatne składowe zawsze z prefiksem `_`.

```python
class Workflow(AggregateRoot["WorkflowId"]):
    # 1. PUBLICZNE — metody i properties
    @property
    def status(self) -> Status:
        return self._status

    def start_at(self, ...) -> None:
        ...

    def finish(self, ...) -> None:
        ...

    # 2. PRYWATNE — z prefiksem _
    def _build_sequence_transitions(self, ...) -> None:
        ...
```

### Zasady

1. **Wszystkie prywatne składowe klasy (`_metoda`, `_atrybut`) występują po wszystkich publicznych.**
2. Wyjątek: `__init__` i `__slots__` mogą być na początku klasy (przed publicznymi metodami).
3. **Żadna publiczna metoda nie występuje po prywatnej.**
4. Prywatne atrybuty instancji (`self._nazwa`) zawsze z prefiksem `_`.
5. Protected (`_` bez name manglingu) i private (`__` z name manglingiem) — używaj `_` (protected), chyba że chcesz name mangling w podklasach.

### Zakres widoczności — prywatne tylko wewnątrz klasy/pliku

Składowe z prefiksem `_` **mogą być używane wyłącznie wewnątrz klasy która je definiuje** lub — w przypadku funkcji/modutu — **wewnątrz tego samego pliku**.

```python
# POPRAWNIE — użycie wewnątrz tej samej klasy
class Workflow:
    def finish(self, now):
        self._transition_to(Status.done())  # _ wywołane wewnątrz klasy

    def _transition_to(self, status):
        self._status = status

# ŹLE — użycie z zewnątrz
workflow = Workflow(...)
workflow._transition_to(Status.done())  # ❌ nie wolno — _ to szczegół implementacji
```

**Wyjątki (dozwolone):**
- Testy jednostkowe mogą wołać `_` metody aby zweryfikować stan wewnętrzny — ale tylko w ostateczności, preferuj testowanie przez publiczny API.
- Framework ORM (SQLAlchemy) może wymagać dostępu do `_` pól w mapperach — to akceptowalne w `infrastructure/`.

```python
class Example:
    __slots__ = ("_public_field", "_private_field")

    # PUBLICZNE
    def do_something(self) -> None: ...

    @property
    def value(self) -> str: ...

    # PRYWATNE
    def _helper(self) -> None: ...
```

## Nazewnictwo zmiennych w handlerach

Zmienne w handlerach zawsze opisują co zawierają, nigdy skrótem:

```python
# POPRAWNIE
task_execution = await uow.task_executions.get_by_id(task_execution_id)
graph_execution = await uow.graph_executions.get_by_task_execution_id(task_execution.id)
child_graph_executions = await uow.graph_executions.get_by_parent_id(parent_graph_execution_id)

# ŹLE
te = await uow.task_executions.get_by_id(te_id)
ge = await uow.graph_executions.get_by_task_execution_id(te.id)
children = await uow.graph_executions.get_by_parent_id(pid)
```
