---
name: variable-and-parameter-naming-standards
description: Reguły nazewnictwa zmiennych i parametrów — zakaz skrótów, pełne nazwy biznesowe, lista dozwolonych wyjątków, konwencje dla handlerów i pętli.
---

# Variable and Parameter Naming Standards

> Reguły nazewnictwa zmiennych i parametrów we wszystkich warstwach projektu.

## Podstawowa zasada

**Nigdy nie skracaj nazw zmiennych.** Każda zmienna musi mieć pełną, biznesową nazwę która oddaje jej znaczenie w języku domeny.

Skracanie nazw zmiennych jest zabronione, ponieważ:
1. Zaciera intencję biznesową kodu
2. Wymusza domyślanie się znaczenia przez czytającego
3. Tworzy niespójność — ta sama nazwa w różnych miejscach może oznaczać różne rzeczy
4. Utrudnia refaktoryzację i wyszukiwanie

## Zasada twarda — zero wyjątków

To nie są sugestie ani zalecenia — to **bezwzględnie egzekwowane reguły bez żadnych wyjątków**.

| Status | Przykład | Powód |
|--------|----------|-------|
| ❌ **ZABRONIONE** | `uow` | Musi być `unit_of_work` |
| ❌ **ZABRONIONE** | `cmd` (parametr handlera) | Musi być `command` |
| ✅ **DOZWOLONE** | `command` (parametr handlera) | Standardowa nazwa parametru w Command Handler |
| ✅ **DOZWOLONE** | `event` (parametr handlera) | Standardowa nazwa parametru w Event Handler |
| ✅ **DOZWOLONE** | `query` (parametr handlera) | Standardowa nazwa parametru w Query Handler |
| ❌ **ZABRONIONE** | `id_gen` | Musi być `id_generator` |
| ❌ **ZABRONIONE** | `repo` | Musi być `repository` |
| ❌ **ZABRONIONE** | `ctx` | Musi być `context` (lepiej konkretnie: `sub_graph_context`) |
| ❌ **ZABRONIONE** | `args` | Musi być `arguments` (lepiej konkretnie: `type_arguments`) |
| ❌ **ZABRONIONE** | `dto` jako zmienna | Musi być opisane: `graph_definition_dto` |
| ❌ **ZABRONIONE** | `exc` | Musi być `exception` |

Wszystkie powyższe są **bezwzględnie zabronione** — również w handlerach, serwisach, testach, fixture'ach, conftestach, containerach DI, adapterach i całej infrastrukturze.

To oznacza również, że **nie ma listy "dozwolonych skrótów"** — lista wyjątków poniżej jest wyczerpująca i zamknięta.

## Przykłady ZABRONIONE

| SKRÓCONA (ZABRONIONA) | Problem |
|----------------------|---------|
| `wf_id` | Nie wiadomo czy `workflow_id` czy `workflow_instance_id` |
| `env_id` | Czy `envelope_id` czy `environment_id`? |
| `parent_id` | Czy `parent_graph_execution_id` czy `parent_workflow_id`? |
| `msg_id` | `message_id` to pełna nazwa |
| `gd` | `graph_definition` to pełna nazwa |
| `nd` / `node_dto` | `node_definition` — sufiks `dto` mylący gdy to nie DTO |
| `dto` | Zawsze opisz co za DTO: `graph_definition_dto` |
| `def_id` | `definition_id` lub `graph_definition_id` |
| `command` | Standardowa nazwa parametru w Command Handler |
| `event` | Standardowa nazwa parametru w Event Handler |
| `query` | Standardowa nazwa parametru w Query Handler |
| `ctx` | `context` — lepiej opisać: `sub_graph_context` |
| `args` | `arguments` — lepiej opisać: `type_arguments` |
| `wf` | `workflow` |
| `res` / `ret` | `result` (lub `execution_result`, `query_result`) |
| `stmt` (poza infrastructure) | W domenie/aplikacji to nie biznesowe |
| `te` | `task_execution` |
| `ge` | `graph_execution` |
| `children` | `child_graph_executions` |
| `uow` | `unit_of_work` — to absolutnie najczęstsze naruszenie |
| `id_gen` | `id_generator` |
| `repo` | `repository` |
| `auth` | `authorization_service` / `authentication_service` |
| `cust_id` | `customer_id` |
| `invnum` | `invoice_number` |
| `credit_amt` | `credit_amount` |
| `spec` | `specification` |
| `exc` | `exception` |

## Przykłady PRAWIDŁOWE

```python
# ZAMIAST:
wf_id = WorkflowId(cmd.workflow_id)
# PISZ:
workflow_id = WorkflowId(command.workflow_id)

# ZAMIAST:
parent_id = graph_execution.parent_graph_execution_id
# PISZ:
parent_graph_execution_id = graph_execution.parent_graph_execution_id

# ZAMIAST:
gd = await self._definition_provider.get_graph_definition(def_id)
# PISZ:
graph_definition = await self._definition_provider.get_graph_definition(definition_id)

# ZAMIAST:
for node_dto in graph_definition.node_execution_definitions:
# PISZ:
for node_definition in graph_definition.node_execution_definitions:
```

## Parametry handlerów

Parametr metody `handle` w handlerach **musi** mieć nazwę według typu handlera:

| Handler | Nazwa parametru |
|---------|----------------|
| Command Handler | `command` |
| Event Handler | `event` |
| Query Handler | `query` |

```python
# POPRAWNIE — standardowa nazwa wg typu handlera
async def handle(self, command: StartWorkflowCommand) -> None: ...
async def handle(self, event: WorkflowCompletedEvent) -> None: ...
async def handle(self, query: GetWorkflowQuery) -> None: ...

# ŹLE — opisowa/indywidualna nazwa
async def handle(self, start_workflow_command: StartWorkflowCommand) -> None: ...
```

## Zmienne w handlerach

Zmienne w handlerach zawsze opisują co zawierają, nigdy skrótem:

```python
# POPRAWNIE
task_execution = await unit_of_work.task_execution_repository.get_by_id(task_execution_id)
graph_execution = await unit_of_work.graph_execution_repository.get_by_task_execution_id(task_execution.id)
child_graph_executions = await unit_of_work.graph_execution_repository.get_by_parent_id(parent_graph_execution_id)
```

## ID variables

Zmienne przechowujące identyfikatory zawsze z sufiksem `_id`:

- `workflow_id`
- `task_execution_id`
- `graph_execution_id`
- `graph_definition_id`
- `definition_id`
- `correlation_id`
- `causation_id`

## Zmienna pętli

Jeśli pętla iteruje po kolekcji biznesowej (lista węzłów, lista zadań), zmienna pętli **musi** mieć pełną nazwę biznesową:

```python
# POPRAWNIE:
for node_definition in node_definitions:

# ŹLE:
for nd in nodes:
```

## Wyjątki (dozwolone skróty) — lista zamknięta

**Tylko te poniższe są dozwolone. Żadne inne skróty nie są akceptowane.**

| Wyjątek | Kiedy dozwolony | Przykład |
|---------|----------------|----------|
| `e` | Tylko w klauzuli `except` | `except Exception as e:` |
| `index` | Pętle czysto matematyczne | `for index in range(count):` |
| `_` | Throwaway (nieużywana wartość) | `for _ in range(n):` |
| `self`, `cls` | Metody klas | Słowa kluczowe Python |
| `session` | Infrastructure persistence | ORM standard |
| `stmt` | Infrastructure persistence | ORM standard (SQLAlchemy) |
| `conn` | Infrastructure persistence | Połączenie z bazą danych |
| `engine` | Infrastructure persistence | Silnik SQLAlchemy |

**Konsekwencja naruszenia:** kod z jakimkolwiek skrótem spoza powyższej listy nie przejdzie code review i nie zostanie zaakceptowany do merge.
