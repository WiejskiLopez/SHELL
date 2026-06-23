# Plan naprawy: Value Objects w całej domenie

## Strategy

- **Zero tolerancji** dla typów prostych (`str`, `int`, `bool`, `datetime`) w warstwie **domain**.
- Legacy nie utrzymujemy — refaktorujemy lub wywalamy.
- Aplikacja (`shell/application/`) może używać typów prostych w komendach/DTAs — mapper aplikacyjny mapuje do VO.
- Infrastruktura (`shell/infrastructure/`) mapuje VO na kolumny DB — VO muszą być czyste.
- `GraphNodeTransitionDefinition` zostaje jako `@dataclass(slots=True)` (entity-like), nie VO.

---

## Phase 0 — Nowe uniwersalne VO na platformie

Tworzymy brakujące VO z tabeli wzorca, używane przez wiele domen.

| VO | Typ | Plik docelowy |
|----|-----|---------------|
| `Enabled` | `bool` + walidacja + factory `yes()/no()` | `shell/domain/platform/value_objects/enabled.py` |
| `CreatedAt` | `Timestamp` (kompozycja) | `shell/domain/platform/value_objects/created_at.py` |
| `UpdatedAt` | `Timestamp` (kompozycja) | `shell/domain/platform/value_objects/updated_at.py` |
| `Goal` | `str` + walidacja niepustości + max 500 znaków | `shell/domain/platform/value_objects/goal.py` |
| `Purpose` | `str` + walidacja niepustości | `shell/domain/platform/value_objects/purpose.py` |
| `ActionRef` | `str` + niepustość | `shell/domain/platform/value_objects/action_ref.py` |
| `ArtifactUri` | `str` + walidacja URI | `shell/domain/platform/value_objects/artifact_uri.py` |
| `ArchiveUri` | `str` + walidacja URI | `shell/domain/platform/value_objects/archive_uri.py` |
| `SequenceId` | `int` + `>= 0` | `shell/domain/platform/value_objects/sequence_id.py` |
| `Step` | `int` + `>= 0` | `shell/domain/platform/value_objects/step.py` |
| `IntervalSeconds` | `float` + `> 0` | `shell/domain/platform/value_objects/interval_seconds.py` |
| `BatchSize` | `int` + `> 0` | `shell/domain/platform/value_objects/batch_size.py` |
| `TriggerEventId` | `str` + niepustość | `shell/domain/platform/value_objects/trigger_event_id.py` |
| `Error` | `str` + niepustość (dla błędów scheduler) | `shell/domain/platform/value_objects/error.py` |

---

## Phase 1 — Naprawa istniejących VO

### 1.1. VO bez walidacji — dodać `__post_init__`

| Plik | Zmiana |
|------|--------|
| `task_description.py` | dodać `__post_init__` – niepustość |
| `skill_payload.py` | dodać `__post_init__` – dict nie może być pusty? (zależy od biznesu) |
| `identity.py` | dodać `__post_init__` – dict nie może być pusty |
| `config.py` | dodać `__post_init__` – temperature [0.0, 2.0], max_tokens > 0, top_p (0.0, 1.0] |
| `environment.py` | dodać `__post_init__` – os, runtime, cwd niepuste |
| `execution_policy.py` | dodać `__post_init__` – max_concurrent >= 1, timeout >= 0, retry_count >= 0 |
| `action_config.py` | dodać `__post_init__` – action_type niepuste, walidacja krzyżowa |
| `trigger_config.py` | dodać `__post_init__` – source_context, trigger_event_type niepuste |
| `repo_url.py` | dodać `__post_init__` – walidacja formatu URL (regex), `None` dozwolone |

### 1.2. VO z brakującym `frozen=True, slots=True`

| Plik | Zmiana |
|------|--------|
| `graph_execution_definition.py` | dodać `frozen=True, slots=True` do obu klas, zastąpić `list[...]` przez `tuple[...]` |
| `manifest.py` | `role: str`, `node_type: str`, `version: str` → zastąpić VO (NodeRole, NodeType, Version*) |
| `environment.py` | `os: str`, `runtime: str`, `cwd: str` → zastąpić VO (Os, Runtime, Cwd) lub zostawić z walidacją |

### 1.3. VO anemiczne — dodać factory methods + logikę biznesową

| VO | Factory / Behavior |
|----|--------------------|
| `WorkDir` | `@classmethod default()`, `@classmethod from_path()` |
| `TaskName` | `@classmethod of(name: str)` |
| `EventOutput` | `@classmethod empty()` |
| `ErrorDescription` | `@classmethod of(msg: str)` |
| `Reason` | dodać `__str__`, `@classmethod empty()` |
| `Config` | `@classmethod default()`, `with_model()`, `with_temperature()` |
| `Environment` | `@classmethod detect()` |
| `SkillPayload` | `@classmethod empty()`, `merge(other)`, `get(key)` |
| `Identity` | `@classmethod anonymous()`, `get(key)` |

---

## Phase 2 — Klasy które nie dziedziczą po ValueObject → refaktor

### 2.1. `LoopCounter`
**Plik:** `execution/aggregates/graph_execution/value_objects/loop_counter.py`

**Problem:** Mutable, brak `ValueObject`, `transition_id: str`, `max_loop_count: int`.
**Fix:** 
- Przemianować na `LoopCounter` → VO `@dataclass(frozen=True, slots=True)` extends ValueObject
- `transition_id: GraphNodeTransitionExecutionId`, `current_iteration: int`, `max_loop_count: int`
- `increment()` → zwraca nowy `LoopCounter`, nie mutuje
- `is_exhausted` → property (czysta funkcja, działa na frozen)
- Aktualizować `GraphExecution.get_or_create_loop_counter()` aby zwracała nowy obiekt przy każdej iteracji zamiast mutować

### 2.2. `SpawnSpec`
**Plik:** `execution/aggregates/graph_node_transition_execution/value_objects/spawn_spec.py`

**Problem:** Brak `ValueObject`, `goal: str` (powinno być `Goal`), `skills: tuple[dict[str, Any], ...]` (powinno być kolekcją `SkillPayload`).
**Fix:**
- `@dataclass(frozen=True, slots=True)` extends `ValueObject`
- `goal: Goal` zamiast `str`
- `skills: tuple[SkillPayload, ...]` zamiast `tuple[dict, ...]`
- `target_role: NodeRole | None`

### 2.3. `PolicyAction`, `ContinueDecision`, `AbortDecision`
**Pliki:** `execution/services/graph_node_execution_policy/`

**Problem:** Klasy marker/decyzji bez `ValueObject`.
**Fix:**
- `PolicyAction` → `@dataclass(frozen=True, slots=True)` extends `ValueObject`, dodać pole `decision_type: str`
- `ContinueDecision` → extends `PolicyAction` (już jako VO) lub zrobić prosty VO
- `AbortDecision` → jw, `reason: Reason` zamiast `str`

---

## Phase 3 — Domenowe aggregate'y — wymiana typów prostych na VO

### 3.1. Workflow (`workflow.py`)

| Pole/Metoda | Obecnie | Docelowo |
|------------|---------|----------|
| `_created_at` | `datetime` | `CreatedAt` |
| `start_at(now: datetime)` | `datetime` | `Timestamp` |
| `finish(now: datetime)` | `datetime` | `Timestamp` |
| `abort(reason: str, now: datetime)` | `str` | `Reason`, `Timestamp` |
| `add_skill(payload, now: datetime)` | `datetime` | `Timestamp` |
| `add_state_input(payload, now: datetime)` | `datetime` | `Timestamp` |
| `add_state_output(payload, now: datetime)` | `datetime` | `Timestamp` |

### 3.2. Envelope (`envelope.py`)

| Pole/Metoda | Obecnie | Docelowo |
|------------|---------|----------|
| `correlation_id` | `str` | `CorrelationId` |
| `source_role` | `str` | `NodeRole` |
| `target_role` | `str` | `NodeRole` |
| `sequence_id` | `int` | `SequenceId` |
| `step` | `int` | `Step` |
| `payload` | `dict[str, object]` | `SkillPayload` |
| `artifact_uri` | `str` | `ArtifactUri` |
| `archive_uri` | `str` | `ArchiveUri` |
| `created_at` | `datetime` | `CreatedAt` |
| `updated_at` | `datetime` | `UpdatedAt` |
| `new(..., correlation_id: str, ...)` | `str` | `CorrelationId` |
| `new(..., source_role: str, target_role: str, ...)` | `str` | `NodeRole` |
| `new(..., sequence_id: int, step: int, ...)` | `int` | `SequenceId`, `Step` |
| `new(..., payload: dict, now: datetime, ...)` | `dict` | `SkillPayload \| None`, `Timestamp` |

### 3.3. GraphExecution (`graph_execution.py`)

| Pole/Metoda | Obecnie | Docelowo |
|------------|---------|----------|
| `_correlation_id` | `str` | `CorrelationId` |
| `_graph_definition_id` | `str` | `GraphDefinitionId` |
| `_tags` | `dict` | `Tags` (nowe VO kolekcyjne) |
| `_workflow_id` | `Any` | `WorkflowId` |
| `depth: int` (param) | `int` | `GraphDepth` (już jest, ale zmienić typ parametru) |
| `start_planning(now: datetime)` | `datetime` | `Timestamp` |
| `plan_complete(plan, now: datetime)` | `datetime` | `Timestamp` |
| `complete(verifier_result, now: datetime)` | `datetime` | `Timestamp` |
| `fail(reason, now: datetime)` | `datetime` | `Timestamp` |
| `mark_verifying(now: datetime)` | `datetime` | `Timestamp` |
| `absorb_child_results(..., now: datetime)` | `datetime` | `Timestamp` |

Usunąć legacy:
- `_graph_definition_id`, `_graph_node_execution_ids`, `_graph_node_execution_objects`, `_transitions`, `_loop_counters`, `_state_input`, `_state_output`, `_timeout_at`, `_correlation_id`, `_tags`, `_workflow_id`
- Wszystkie legacy metody: `add_transition`, `add_graph_node_execution_id`, `get_outgoing_transitions`, `get_incoming_transitions`, `get_or_create_loop_counter`, `from_graph_definition`
- Legacy properties: `state_input`, `state_output`, `graph_node_execution_ids`, `graph_node_executions`, `transitions`, `loop_counters`, `workflow_id`, `graph_definition_id`

> Uwaga: `from_graph_definition` jest wywoływany w `sub_graph_execution_service.py` → przed usunięciem przenieść logikę do serwisu.

### 3.4. GraphNodeExecution (`graph_node_execution.py`)

Usunąć legacy:
- `position`, `mode`, `node_type`, `model`, `command`, `_legacy_timeout`, `retries`, `log_level`, `max_step`, `no_ask_user`, `autopilot`, `task_execution_id`, `source_dir`, `status_initial`, `timeout_seconds`, `max_retries`, `retry_delay_seconds`

Zostawić V3:
- `_graph_execution_id`, `_order`, `_role`, `_status`, `_state_inputs`, `_state_outputs`

Wszystkie pola legacy w konstruktorze → usunąć.

### 3.5. TaskExecution (`task_execution.py`)

| Pole/Metoda | Obecnie | Docelowo |
|------------|---------|----------|
| `_created_at` | `Any` | `CreatedAt` |
| `complete(output: str, now: datetime)` | `str` | `EventOutput`, `Timestamp` |
| `prepare_workspace(path: str)` | `str` | `WorkDir` (już) |

Usunąć legacy:
- `created_at` property (Any → zastąpione `CreatedAt`)

### 3.6. Session (`session.py`)

| Pole/Metoda | Obecnie | Docelowo |
|------------|---------|----------|
| `_opened_at` | `datetime` | `CreatedAt` |
| `_closed_at` | `datetime \| None` | `UpdatedAt \| None` |
| `open(now: datetime, goal: str)` | `datetime` | `Timestamp`, `Goal` |
| `add_skill(payload, now: datetime)` | `datetime` | `Timestamp` |
| `close(now: datetime)` | `datetime` | `Timestamp` |

### 3.7. User (`user.py`)

| Pole/Metoda | Obecnie | Docelowo |
|------------|---------|----------|
| `enable() / disable()` | `ValueError` ze stringiem | bez zmian (exception OK, ale tekst powinien być `ErrorDescription` lub `Reason`) |

### 3.8. Project (`project.py`)

Bez zmian — już dobrze.
`archive() / activate()` — jw.

### 3.9. SchedulerExecution (`scheduler_execution.py`)

| Pole/Metoda | Obecnie | Docelowo |
|------------|---------|----------|
| `_trigger_event_id` | `str \| None` | `TriggerEventId \| None` |
| `_trigger_event_type` | `str \| None` | nowe VO `TriggerEventType` lub `str` jako prosty typ (wg decyzji — to ID eventu, może być prosty) |
| `_action_ref` | `str \| None` | `ActionRef \| None` |
| `_action_ref_type` | `str \| None` | `ActionRefType` (nowe VO) |
| `_error` | `str \| None` | `Error \| None` |
| `_started_at` | `datetime \| None` | `Timestamp \| None` |
| `_completed_at` | `datetime \| None` | `Timestamp \| None` |
| `_created_at` | `datetime` | `CreatedAt` |
| `_updated_at` | `datetime` | `UpdatedAt` |
| `start(action_ref, action_ref_type, now)` | `str, str, datetime` | `ActionRef, ActionRefType, Timestamp` |
| `complete(output_state, now)` | `dict, datetime` | `SkillPayload, Timestamp` |
| `fail(error, now)` | `str, datetime` | `Error, Timestamp` |
| `skip(reason, now)` | `str, datetime` | `Reason, Timestamp` |

### 3.10. SchedulerDefinition (`scheduler_definition.py`)

| Pole/Metoda | Obecnie | Docelowo |
|------------|---------|----------|
| `_name` | `str` | `TaskName` lub nowe `SchedulerName` |
| `_description` | `str \| None` | `TaskDescription \| None` |
| `_enabled` | `bool` | `Enabled` |
| `_created_at` | `datetime` | `CreatedAt` |
| `_updated_at` | `datetime` | `UpdatedAt` |
| `matches_trigger(source_context, trigger_event_type)` | `str, str` | VOs |

### 3.11. SchedulerJob (`scheduler_job.py`)

| Pole/Metoda | Obecnie | Docelowo |
|------------|---------|----------|
| `_name` | `str` | `SchedulerName` |
| `_job_type` | `str` | `JobType` (nowe VO) |
| `_interval_seconds` | `float` | `IntervalSeconds` |
| `_batch_size` | `int` | `BatchSize` |
| `_enabled` | `bool` | `Enabled` |
| `_config` | `dict[str, Any]` | `SkillPayload` lub `Config` |
| `_created_at` | `datetime` | `CreatedAt` |
| `_updated_at` | `datetime` | `UpdatedAt` |

### 3.12. GraphDefinition entity (`definition/entities/graph_definition.py`)

| Pole/Metoda | Obecnie | Docelowo |
|------------|---------|----------|
| `name` | `str` | `TaskName` |
| `purpose` | `str` | `Purpose` |
| `get_graph_node_definition(position)` | `int` | `NodeOrder` |

### 3.13. GraphNodeDefinition entity (`definition/entities/graph_node_definition.py`)

| Pole | Obecnie | Docelowo |
|------|---------|----------|
| `position` | `int` | `NodeOrder` (zastąpić typ, nie usuwać pola) |
| `role` | `str` | `NodeRole` |
| `node_type` | `str` | `NodeType` (nowe VO) |
| `model` | `str` | `Model` (nowe VO) |
| `command` | `str` | `Command` (nowe VO) |
| `timeout` | `int` | `Timeout` (nowe VO) |
| `retries` | `int` | `RetryCount` (nowe VO) |
| `log_level` | `str` | `LogLevel` (nowe VO) |
| `max_step` | `int \| None` | `MaxStep` (nowe VO) |
| `no_ask_user` | `bool` | `Enabled` (nowe) |
| `autopilot` | `bool` | `Enabled` |
| `status_initial` | `str` | `Status` lub `GraphNodeExecutionStatus` |
| `script` | `str` | `Script` (nowe VO) |
| `script_type` | `str` | `ScriptType` (nowe VO) |

### 3.14. GraphNodeTransitionDefinition entity (`definition/entities/graph_node_transition_definition.py`)

| Pole | Obecnie | Docelowo |
|------|---------|----------|
| `priority` | `int` | `Priority` (nowe VO) |
| `condition_expression` | `str \| None` | `ConditionExpression` (nowe VO) |
| `condition_language` | `str \| None` | `ConditionLanguage` (już istnieje na platformie) |
| `max_loop_count` | `int` | `MaxLoopCount` (nowe VO) |
| `timeout_seconds` | `int \| None` | `Timeout \| None` |
| `retry_count` | `int` | `RetryCount` |
| `retry_delay_seconds` | `int` | `RetryDelay` (nowe VO) |
| `data_mapping` | `dict[str, str] \| None` | `DataMapping` (nowe kolekcyjne VO) |
| `label` | `str` | `Label` (nowe VO) |

### 3.15. RunnerConfig entity (`definition/entities/runner_config.py`)

| Pole | Obecnie | Docelowo |
|------|---------|----------|
| `_package_name` | `str` | `PackageName` (nowe VO) |
| `_kind` | `str` | `Kind` (nowe VO) |
| `_body` | `dict[str, object]` | `ConfigurationBody` (nowe VO) |
| `_created_at` | `datetime` | `CreatedAt` |

### 3.16. TaskExecutionStateInput / TaskExecutionStateOutput

| Pole | Obecnie | Docelowo |
|------|---------|----------|
| `_is_current` | `bool` | `Enabled` |
| `_created_at` | `datetime` | `CreatedAt` |

### 3.17. GraphExecutionStateOutput

| Pole | Obecnie | Docelowo |
|------|---------|----------|
| `_is_current` | `bool` | `Enabled` |
| `_created_at` | `datetime` | `CreatedAt` |

---

## Phase 4 — Eventy — wymiana typów prostych na VO

### 4.1. DomainEvent base (`platform/events/domain_event.py`)

| Pole/Metoda | Obecnie | Docelowo |
|------------|---------|----------|
| `occurred_at` | `datetime` | `Timestamp` |
| `from_payload(occurred_at: datetime, ...)` | `datetime` | `Timestamp` |

### 4.2. Wszystkie eventy

We wszystkich eventach:
- `now: datetime` w factory methods → `now: Timestamp`
- Wszystkie `reason: str` → `Reason`
- Wszystkie `error: str` → `ErrorDescription`
- `description: str` → `TaskDescription`
- `goal: str` → `Goal`
- `depth: int` → `GraphDepth`
- `current_cycle: int` → `PlanningCycle`
- `max_planning_cycles: int` → `MaxPlanningCycles`
- `output: str` → `EventOutput`

Lista eventów do przerobienia:

| Event | Pole | Nowe VO |
|-------|------|---------|
| `GraphExecutionCreatedEvent` | `goal: str`, `depth: int` | `Goal`, `GraphDepth` |
| `GraphSpawnedEvent` | `goal: str` | `Goal` |
| `GraphNodeExecutionFailedEvent` (workflow) | `reason: str` | `Reason` |
| `TaskExecutionCreatedEvent` | `description: str`, `skills: list[dict]` | `TaskDescription`, `tuple[SkillPayload, ...]` |
| `TaskExecutionExhaustedEvent` | `current_cycle: int`, `max_planning_cycles: int` | `PlanningCycle`, `MaxPlanningCycles` |
| `TaskExecutionCompletedEvent` | `output: str` | `EventOutput` |
| `EnvelopeDeadletteredEvent` | `reason: str` | `Reason` |
| `SchedulerExecutionSkippedEvent` | `reason: str` | `Reason` |
| `SchedulerExecutionFailedEvent` | `error: str` | `Error` |

---

## Phase 5 — Domenowe serwisy — wymiana typów prostych w sygnaturach

We wszystkich serwisach domenowych (`shell/domain/.../services/`):
- `now: datetime` → `Timestamp`
- `graph_definition_id: str` → `GraphDefinitionId`
- `correlation_id: str` → `CorrelationId`
- `reason: str` → `Reason`
- `error: str` → `ErrorDescription`
- `goal: str` → `Goal`
- `output: str` → `EventOutput`

### 5.1. `SubGraphExecutionService.spawn()`
- `graph_definition_id: str` → `GraphDefinitionId`
- `correlation_id: str` → `CorrelationId`
- `parent_graph_execution_id_value: str` → `GraphExecutionId`

### 5.2. `GraphExcetutionRoutingService`
- `target_role: str | None` → `NodeRole | None`

### 5.3. `ConditionEvaluator` (protocol)
- `language: str | None` → `ConditionLanguage | None`

### 5.4. `SimpleConditionEvaluator`
- `language: str | None` → `ConditionLanguage | None`

### 5.5. `GraphNodeExecutionPolicy`
- `reason: str` → `Reason`

### 5.6. `FailFastGraphNodeExecutionPolicy`
- `reason: str` → `Reason`

### 5.7. `AbortDecision`
- `reason: str` → `Reason`

### 5.8. `SchedulerOrchestrator`
- `trigger_event_id: str | None` → `TriggerEventId | None`
- `trigger_event_type: str | None` → `str` lub VO
- `input_state: dict[str, Any] | None` → `SkillPayload | None`
- `action_ref: str`, `action_ref_type: str` → `ActionRef`, `ActionRefType`
- `output_state: dict[str, Any] | None` → `SkillPayload | None`
- `error: str | None` → `Error | None`

### 5.9. `PendingGraphFinder`
- parametr `limit: int` → zostaje (limit to szczegół implementacyjny, nie domenowy)

### 5.10. `DualLayerDispatcher`
- `event_id: str` → `TriggerEventId`

### 5.11. `EnvelopeLifecycleService`
- `max_step: int` → `Step`

### 5.12. `RagIndexService`
- `chunk_size: int`, `overlap: int` → zostają int (szczegóły techniczne)
- `source_uri: str`, `title: str`, `domain: str` → zostają (ale można zrobić VO dla kompletności — `SourceUri`, `Title`, `Domain`)

---

## Phase 6 — Kolekcyjne VO (reguła 7)

Dla kolekcji o znaczeniu biznesowym w agregatach:
- `Skills` → `@dataclass(frozen=True, slots=True)` opakowujący `tuple[Skill, ...]` z metodami `add()`, `remove()`, `__iter__`
- `StateInputs`, `StateOutputs` → analogicznie
- `Tags` → dla `GraphExecution._tags` (jeśli nie wywalone)

---

## Phase 7 — Nowe VO dla pojęć domenowych (odpowiedź na pytanie 6)

| VO | Typ | Walidacja | Zachowanie |
|----|-----|-----------|------------|
| `NodeType` | `str` | niepuste | — |
| `Model` | `str` | niepuste | — |
| `Command` | `str` | niepuste | — |
| `Timeout` | `int` | `>= 0` | `@classmethod default()` |
| `LogLevel` | `str` | `in {"DEBUG","INFO","WARN","ERROR"}` | — |
| `MaxStep` | `int \| None` | `>= 0` | — |
| `Script` | `str` | niepuste | — |
| `ScriptType` | `str` | niepuste | — |
| `PackageName` | `str` | niepuste + regex `^[a-z_][a-z0-9_]*$` | — |
| `Kind` | `str` | niepuste | — |
| `Priority` | `int` | `>= 0` | — |
| `ConditionExpression` | `str` | niepuste | — |
| `RetryCount` | `int` | `>= 0` | — |
| `RetryDelay` | `int` | `>= 0` | — |
| `MaxLoopCount` | `int` | `>= 0` | — |
| `Label` | `str` | dowolna | — |
| `DataMapping` | kolekcja dict | walidacja kluczy | — |
| `JobType` | `str` (StrEnum) | `"messaging"`, `"polling"`, `"webhook"` | — |
| `ConfigurationBody` | `dict` | walidacja struktury | `get()`, `set()` |

---

## Phase 8 — Usunięcie deprecated kodu

| Plik | Powód | Zastąpienie |
|------|-------|-------------|
| `platform/value_objects/mode.py` | deprecated → `NodeRole` | Migracja wszystkich referencji do `NodeRole` |
| `platform/value_objects/status.py` | deprecated → dedykowane statusy | Migracja referencji |
| `platform/value_objects/transition_type.py` | deprecated → `EdgeType` | Migracja referencji |

### Referencje do usuniętych VO:

1. `Mode` używane w:
   - `manifest.py` → zmienić na `NodeRole`
   - `graph_execution.py` (legacy `from_graph_definition`, `graph_node_executions`) → usunąć wraz z legacy
   - `sub_graph_execution_service.py` → zmienić na `NodeRole`
   - `graph_node_definition.py` → zostawić `Mode` bo tam jest poprawnie używane (to entity definicji), ale rozważyć czy nie przejść na `NodeRole`

2. `Status` używane w:
   - `run_graph_node_execution_handler.py` (app layer) → OK, app warstwa
   - `save_graph_node_execution_result_handler.py` (app layer) → OK

3. `TransitionType` używane w:
   - `graph_node_transition_definition.py` → zmienić na `EdgeType`

---

## Phase 9 — Domain service dla GraphExecution → sub_graph_execution_service

`from_graph_definition` w `GraphExecution` zostaje usunięty. Logika przeniesiona do `SubGraphExecutionService.spawn()` gdzie już jest.

---

## Dependencies między fazami

```
Phase 0 (nowe VO platformy)
  └─ Phase 1 (naprawa istniejących VO)
       └─ Phase 2 (brakujące ValueObject)
            └─ Phase 3 (agregaty)
            │    └─ Phase 4 (eventy)
            └─ Phase 5 (serwisy)
                 └─ Phase 6 (kolekcje)
                      └─ Phase 7 (nowe VO domenowe)
                           └─ Phase 8 (usunięcie deprecated)
                                └─ Phase 9 (przeniesienie logiki)
```

Fazy można realizować równolegle tylko jeśli dotyczą różnych plików.
Phase 0 jest warunkiem wstępnym dla reszty — nowe VO muszą istnieć zanim agregaty/eventy zaczną je importować.

---

## Uwagi końcowe

1. **Infrastruktura** (SQLAlchemy mappery) będzie wymagać aktualizacji po każdej zmianie VO — każdy VO z nowym typem opakowanym wymaga nowego typu kolumny lub konwertera.
2. **Nie zmieniamy** plików w `shell/application/`, `shell/infrastructure/`, `shell/framework/` w ramach tego planu — one mapują się same później.
3. Każda zmiana agregatu/encji wymaga aktualizacji odpowiadającego mu repozytorium in-memory i SQL.
4. `TaskName` istnieje w `execution/value_objects/` — nowe `SchedulerName` może być aliasem lub osobnym VO.
5. Wszystkie nowe VO tworzymy na platformie (`shell/domain/platform/value_objects/`) jeśli używane przez 2+ domen — w domenie (`shell/domain/<domain>/value_objects/`) jeśli specyficzne.
