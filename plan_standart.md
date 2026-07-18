# Plan standaryzacji agregatów SHELL
> Ujednolicenie wszystkich agregatów do wspólnego minimum + poprawki znalezionych odstępstw.

## Zasady wspólne

Każdy agregat MUSI mieć:

1. `__slots__` ze wszystkimi polami (oprócz `_id` — dziedziczony z AggregateRoot)
2. `_created_at: CreatedAt` — ustawiane w `new()`, nigdy później zmieniane
3. `_updated_at: UpdatedAt` = `_created_at` przy starcie, aktualizowane przy każdej mutacji
4. `_deleted_at: DeletedAt | None` — soft-delete (opcjonalnie, ale zalecane)
5. `new()` — factory method, generuje ID + ustawia timestamps + **bezwarunkowo emituje `{Name}CreatedEvent`**
6. `restore()` — rekonstrukcja z DB, **bez walidacji, bez eventów**
7. Factory method nazywa się `new()` (nie `create()`, nie `open()`, nie `initialize()`)
8. Każda mutacja: guard → mutate → `append_event()`
9. Event bezwarunkowy — nigdy `if now is not None: append_event(...)`
10. ORM Model → Mapper (entity→model, model→entity) → SQL Repository → InMemory Repository
11. DTO → Command + Handler → Query + Handler → Router (POST / + GET /{id}) → Monolith
12. Tag OpenAPI w routerze + w `openapi.py`

---

## Punkt 1: `_updated_at` — dodać do agregatów które go nie mają

### Kryterium
Agregat nie ma `_updated_at` → dodać.

### Lista

| # | Agregat | Plik | BC |
|---|---------|------|----|
| 1 | **Session** | `shell/domain/session/aggregates/session/session.py` | session |
| 2 | **SessionState** | `shell/domain/session/aggregates/session_state/session_state.py` | session |
| 3 | **MessageRouter** | `shell/domain/messaging/aggregates/message_router/message_router.py` | messaging |
| 4 | **Workflow** | `shell/domain/execution/aggregates/workflow/workflow.py` | execution |
| 5 | **NodeExecution** | `shell/domain/execution/aggregates/node_execution/node_execution.py` | execution |
| 6 | **TaskExecution** | `shell/domain/execution/aggregates/task_execution/task_execution.py` | execution |
| 7 | **UserExecution** | `shell/domain/execution/aggregates/user_execution/user_execution.py` | execution |
| 8 | **SessionExecution** | `shell/domain/execution/aggregates/session_execution/session_execution.py` | execution |
| 9 | **AgentSkillExecution** | `shell/domain/execution/aggregates/agent_skill_execution/agent_skill_execution.py` | execution |
| 10 | **NodeDefinition** | `shell/domain/definition/aggregates/node_definition/node_definition.py` | definition |
| 11 | **NodeLinkDefinition** | `shell/domain/definition/aggregates/node_link_definition/node_link_definition.py` | definition |
| 12 | **NodeLinkExecution** | `shell/domain/execution/aggregates/node_link_execution/node_link_execution.py` | execution |
| 13 | **RunnerConfig** | `shell/domain/definition/aggregates/runner_config/runner_config.py` | definition |

### Co zmienić w każdym

1. Dodać `_updated_at` do `__slots__`
2. W `__init__`: dodać parametr `updated_at: UpdatedAt`
3. W `new()`: `updated_at=UpdatedAt.from_datetime(now.value)` (też `CreatedAt`)
4. W `restore()`: dodać parametr `updated_at: UpdatedAt`
5. W ORM Model: dodać kolumnę `updated_at: Mapped[datetime]`
6. W mapperach: dodać mapowanie dla `updated_at`
7. Aktualizacja testów

---

## Punkt 2: `_deleted_at` — dodać do agregatów które go nie mają

### Kryterium
Agregat nie ma `_deleted_at` → dodać. Soft-delete to standardowa praktyka audytowa.

### Lista (wszystkie poza User, Project, UserSkill, ProjectSkill, TaskExecution, EdgeExecution, EdgeLinkExecution, GraphExecution)

| # | Agregat | Plik |
|---|---------|------|
| 1 | Session | `shell/domain/session/aggregates/session/session.py` |
| 2 | Workflow | `shell/domain/execution/aggregates/workflow/workflow.py` |
| 3 | NodeExecution | `shell/domain/execution/aggregates/node_execution/node_execution.py` |
| 4 | GraphExecution | `shell/domain/execution/aggregates/graph_execution/graph_execution.py` |
| 5 | SessionExecution | `shell/domain/execution/aggregates/session_execution/session_execution.py` |
| 6 | UserExecution | `shell/domain/execution/aggregates/user_execution/user_execution.py` |
| 7 | AgentExecution | `shell/domain/execution/aggregates/agent_execution/agent_execution.py` |
| 8 | AgentSkillExecution | `shell/domain/execution/aggregates/agent_skill_execution/agent_skill_execution.py` |
| 9 | AgentConfigExecution | `shell/domain/execution/aggregates/agent_config_execution/agent_config_execution.py` |
| 10 | NodeDefinition | `shell/domain/definition/aggregates/node_definition/node_definition.py` |
| 11 | GraphDefinition | `shell/domain/definition/aggregates/graph_definition/graph_definition.py` |
| 12 | GraphDefinitionEmbedding | `shell/domain/definition/aggregates/graph_definition_embedding/graph_definition_embedding.py` |
| 13 | NodeLinkDefinition | `shell/domain/definition/aggregates/node_link_definition/node_link_definition.py` |
| 14 | NodeLinkExecution | `shell/domain/execution/aggregates/node_link_execution/node_link_execution.py` |
| 15 | RunnerConfig | `shell/domain/definition/aggregates/runner_config/runner_config.py` |
| 16 | MessageRouter | `shell/domain/messaging/aggregates/message_router/message_router.py` |
| 17 | SchedulerDefinition | `shell/domain/scheduling/aggregates/scheduler_definition/scheduler_definition.py` |
| 18 | SchedulerExecution | `shell/domain/scheduling/aggregates/scheduler_execution/scheduler_execution.py` |
| 19 | SchedulerJob | `shell/domain/scheduling/aggregates/scheduler_job/scheduler_job.py` |

### Uwaga
- User, Project, UserSkill, ProjectSkill, TaskExecution, EdgeExecution, EdgeLinkExecution, GraphExecution już mają — nie tykać.

---

## Punkt 3: Bezwarunkowy event w `new()`

### Kryterium
`new()` (lub `create()` / `open()` / `initialize()`) musi bezwarunkowo emitować `{Aggregate}CreatedEvent`.

### Naruszenia

| # | Agregat | Problem | Fix |
|---|---------|---------|-----|
| 1 | **Project** | Brak `ProjectCreatedEvent` — nie emituje nic | Stworzyć `ProjectCreatedEvent` + `append_event()` w `create()` |
| 2 | **NodeDefinition** | `if now is not None: append_event(...)` | Usunąć warunek, zawsze emitować |
| 3 | **GraphDefinition** | `if now is not None: append_event(...)` | Usunąć warunek, zawsze emitować |

### Agregaty bez eventu w factory (do dodania)

| # | Agregat | BC |
|---|---------|----|
| 4 | UserState | user |
| 5 | ProjectState | project |
| 6 | SessionState | session |
| 7 | WorkflowState | execution |
| 8 | NodeExecutionState | execution |
| 9 | GraphExecutionState | execution |
| 10 | TaskExecutionState | execution |
| 11 | SessionExecutionState | execution |
| 12 | UserExecutionState | execution |
| 13 | NodeLinkExecution | execution |
| 14 | AgentExecution | execution |
| 15 | AgentSkillExecution | execution |
| 16 | AgentConfigExecution | execution |
| 17 | NodeLinkDefinition | definition |
| 18 | GraphDefinitionEmbedding | definition |
| 19 | RunnerConfig | definition |
| 20 | MessageRouter | messaging |
| 21 | SchedulerDefinition | scheduling |
| 22 | SchedulerJob | scheduling |
| 23 | SchedulerExecution | scheduling |

### Uwaga do State agregatów
UserState, ProjectState, SessionState, WorkflowState, NodeExecutionState, GraphExecutionState, TaskExecutionState, SessionExecutionState, UserExecutionState — to 9 kopii key-value state. Zostały celowo pominięte w tym planie (decyzja: będzie inaczej w przyszłości).

---

## Punkt 4: Ujednolicenie nazwy factory method na `new()`

### Kryterium
Factory method do tworzenia nowego agregatu nazywa się `new()`.

### Naruszenia

| # | Agregat | Obecna nazwa | Plik |
|---|---------|-------------|------|
| 1 | **User** | `create()` | `shell/domain/user/aggregates/user/user.py` |
| 2 | **UserState** | `create()` | `shell/domain/user/aggregates/user_state/user_state.py` |
| 3 | **UserSkill** | `new()` | ✅ OK |
| 4 | **Project** | `create()` | `shell/domain/project/aggregates/project/project.py` |
| 5 | **ProjectState** | `create()` | `shell/domain/project/aggregates/project_state/project_state.py` |
| 6 | **ProjectSkill** | `new()` | ✅ OK |
| 7 | **Session** | `open()` | `shell/domain/session/aggregates/session/session.py` |
| 8 | **SessionState** | `create()` | `shell/domain/session/aggregates/session_state/session_state.py` |
| 9 | **Workflow** | `create()` | `shell/domain/execution/aggregates/workflow/workflow.py` |
| 10 | **WorkflowState** | `create()` | `shell/domain/execution/aggregates/workflow_state/workflow_state.py` |
| 11 | **NodeExecution** | `new()` | ✅ OK |
| 12 | **NodeExecutionState** | `create()` | `shell/domain/execution/aggregates/node_execution_state/node_execution_state.py` |
| 13 | **GraphExecution** | `initialize()` | `shell/domain/execution/aggregates/graph_execution/graph_execution.py` |
| 14 | **GraphExecutionState** | `create()` | `shell/domain/execution/aggregates/graph_execution_state/graph_execution_state.py` |
| 15 | **TaskExecution** | `create()` | `shell/domain/execution/aggregates/task_execution/task_execution.py` |
| 16 | **TaskExecutionState** | `create()` | `shell/domain/execution/aggregates/task_execution_state/task_execution_state.py` |
| 17 | **SessionExecution** | `create()` | `shell/domain/execution/aggregates/session_execution/session_execution.py` |
| 18 | **SessionExecutionState** | `create()` | `shell/domain/execution/aggregates/session_execution_state/session_execution_state.py` |
| 19 | **EdgeExecution** | `new()` | ✅ OK |
| 20 | **EdgeLinkExecution** | `new()` | ✅ OK |
| 21 | **NodeLinkExecution** | `create()` | `shell/domain/execution/aggregates/node_link_execution/node_link_execution.py` |
| 22 | **EdgeExecution** | `new()` | ✅ OK |
| 23 | **NodeDefinition** | `create()` | `shell/domain/definition/aggregates/node_definition/node_definition.py` |
| 24 | **GraphDefinition** | `create()` | `shell/domain/definition/aggregates/graph_definition/graph_definition.py` |
| 25 | **NodeLinkDefinition** | `create()` | `shell/domain/definition/aggregates/node_link_definition/node_link_definition.py` |
| 26 | **GraphDefinitionEmbedding** | `create()` | `shell/domain/definition/aggregates/graph_definition_embedding/graph_definition_embedding.py` |
| 27 | **RunnerConfig** | `new()` | ✅ OK |
| 28 | **MessageRouter** | `new()` | ✅ OK |
| 29 | **SchedulerDefinition** | `create()` | `shell/domain/scheduling/aggregates/scheduler_definition/scheduler_definition.py` |
| 30 | **SchedulerExecution** | `create()` | `shell/domain/scheduling/aggregates/scheduler_execution/scheduler_execution.py` |
| 31 | **SchedulerJob** | `create()` | `shell/domain/scheduling/aggregates/scheduler_job/scheduler_job.py` |

### Co zmienić
1. W agregacie: rename metody + `@classmethod` → `@classmethod def new(cls, ...)`
2. We wszystkich miejscach które wołają tę metodę (handlery, testy, factory)
3. W `Session`: zmiana `open()` → `new()` (ale zachować starą nazwę jako alias jeśli używana w kodzie zewnętrznym)

---

## Punkt 5: `__slots__` — dodać tam gdzie brakuje

### Naruszenia

| # | Agregat | Plik | BC |
|---|---------|------|----|
| 1 | **GraphDefinition** | `shell/domain/definition/aggregates/graph_definition/graph_definition.py` | definition |

GraphDefinition ma `__slots__ = ()` — puste. Każdy agregat MUSI mieć `__slots__` z wszystkimi polami.

---

## Punkt 6: Mappery SQL — dodać tam gdzie brakują

### Naruszenia (agregat ma ORM Model ale nie ma mapperów)

| # | Agregat | BC | Brakuje |
|---|---------|----|---------|
| 1 | **NodeExecution** | execution | entity→model + model→entity |
| 2 | **SessionState** | session | entity→model + model→entity |
| 3 | **GraphDefinitionEmbedding** | definition | entity→model + model→entity |
| 4 | **AgentExecution** | execution | entity→model + model→entity |
| 5 | **AgentSkillExecution** | execution | entity→model + model→entity |
| 6 | **AgentConfigExecution** | execution | entity→model + model→entity |

### Naruszenia (agregat nie ma SQL Repository)

| # | Agregat | BC |
|---|---------|----|
| 1 | **SessionState** | session |
| 2 | **AgentExecution** | execution |
| 3 | **AgentSkillExecution** | execution |
| 4 | **AgentConfigExecution** | execution |
| 5 | **SchedulerJob** | scheduling |

---

## Punkt 7: API (router + monolit) — dodać tam gdzie brakuje

### Kryterium
Każdy agregat z gotowym SQL Repo powinien mieć minimum `POST /` + `GET /{id}` w monolicie.

### Priorytet

| Priorytet | Agregat | BC | Uzasadnienie |
|-----------|---------|----|-------------|
| **P1** | **MessageRouter** | messaging | Ma pełny domain + SQL + DTO, brak tylko API |
| **P2** | **SchedulerDefinition** | scheduling | Ma pełny domain + SQL + DTO, brak tylko API |
| **P3** | **SchedulerExecution** | scheduling | Ma pełny domain + SQL + DTO, brak tylko API |
| **P4** | **UserSkill** | user | Ma domain + SQL + DTO, brak API |
| **P5** | **ProjectSkill** | project | Ma domain + SQL + DTO, brak API |
| **P6** | **UserState** | user | Ma domain + SQL + DTO, brak API |
| **P7** | **Project** | project | Ma domain + SQL + DTO + GET, brak POST |
| **P8** | **SessionExecution** | execution | Ma domain + SQL + DTO + Cmd/Qry, brak routera |
| **P9** | **UserExecution** | execution | Ma domain + SQL + DTO + Qry, brak routera |
| **P10** | **Workflow** | execution | Ma domain + SQL + DTO + GET, brak POST |
| **P11** | **NodeExecution** | execution | Ma domain + DTO + GET/result, brak POST + mapperów |
| **P12** | **TaskExecution** | execution | Ma domain + SQL + DTO + Qry, brak routera |
| **P13** | **GraphExecution** | execution | Ma domain + SQL + DTO + Qry, brak routera |
| **P14** | **GraphDefinition** | definition | Ma domain + SQL + DTO + GET, brak POST |
| **P15** | **NodeDefinition** | definition | Ma domain + SQL + DTO + Qry, brak routera |
| **P16** | **RunnerConfig** | definition | Ma domain + SQL + DTO + Qry, brak routera |
| **P17** | **GraphDefinitionEmbedding** | definition | Ma domain + SQL, brak mapperów + DTO + API |
| **P18** | **NodeLinkDefinition** | definition | Ma domain + SQL, brak DTO + API |
| **P19** | **NodeLinkExecution** | execution | Ma domain + SQL + DTO, brak API |
| **P20** | **Session** | session | Ma domain + SQL + DTO + GET/history, brak POST |

---

## Kolejność działań

| Faza | Co | Zależność |
|------|----|-----------|
| **1** | Punkty 1-5: domain + eventy (nie wymaga API) | brak |
| **2** | Punkt 6: mappery + SQL repos | 1 (bo zmieniają się pola) |
| **3** | Punkt 7: API (handlery + router) | 2 |
| **4** | Deploy + publikacja `@shell/api-spec` | 3 |
| **5** | Frontend aktualizuje typy | 4 |

---

## Uwagi końcowe

- **State agregaty** (UserState, ProjectState itd. — 9 kopii) celowo pominięte w tym planie. Są świadomie inne i będą zmieniane w przyszłości.
- **SchedulerJob** nie ma żadnej persystencji — wymaga najpierw decyzji architektonicznej (czy w ogóle potrzebuje SQL, czy to tylko aggregate w pamięci).
- **Session** ma specyficzną domenę (otwieranie/zamykanie) — `open()` zamiast `new()` może pozostać jako alias, ale główna factory powinna nazywać się `new()`.
