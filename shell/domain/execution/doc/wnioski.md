# Wnioski strukturalne — domena `execution`

## Wykonane zmiany

### 1. Rozdzielenie TransitionDefinition od GraphNodeTransitionExecution

**Problem**: Klasa `GraphNodeTransitionExecution` istniała w dwóch miejscach:
- `aggregates/graph_execution/entities/graph_node_transition_execution.py` — jako dataclass entity (definition)
- `aggregates/graph_node_transition_execution/graph_node_transition_execution.py` — jako osobny aggregate root z FSM

To naruszało zasadę DDD: agregat nie może być encją wewnątrz innego agregatu.

**Rozwiązanie**:
- Entity dataclass → usunięta
- Zastąpiona przez `TransitionDefinition` VO w `graph_execution/value_objects/`
- `TransitionDefinition` jest ValueObject — nie ma własnej tożsamości, jest częścią `GraphExecution`
- `GraphNodeTransitionExecution` aggregate zachowany — zarządza wykonaniem tranzycji (FSM: EVALUATED → TAKEN/SKIPPED, LOOP)

**Zmienione pliki**:
- `aggregates/graph_execution/value_objects/transition_definition.py` — NOWY
- `aggregates/graph_execution/value_objects/__init__.py` — dodany export
- `aggregates/graph_execution/entities/graph_node_transition_execution.py` — usunięty
- `aggregates/graph_execution/entities/__init__.py` — oczyszczony

### 2. Legacy cleanup w GraphExecution

**Problem**: `GraphExecution` miał ~50% legacy pól (`_graph_definition_id`, `_graph_node_execution_ids`, `_transitions` jako stary typ, `_loop_counters`, `_state_input`, `_state_output`, `_timeout_at`, `_correlation_id`, `_tags`) oraz metody (`from_graph_definition`, `add_graph_node_execution_id` legacy wrapper).

**Rozwiązanie**:
- Usunięto legacy pola: `_state_input`, `_state_output`, `_loop_counters`, `_graph_definition_id`, `_timeout_at`, `_correlation_id`, `_tags`
- `_graph_node_execution_ids` zachowane jako V3 (używane przez nawigatory)
- `_transitions` zmienione na `list[TransitionDefinition]`
- `increment_loop_counter()` usunięta — logika loop przeniesiona do `GraphNodeTransitionExecution`
- `absorb_child_results()` uproszczona — używa `dict` zamiast wewnętrznych encji
- `add_state_input()/add_state_output()` usunięte — state I/O są osobnymi agregatami
- `from_graph_definition()` — usunięta
- `graph_node_executions` property — zachowane (używane przez nawigatory)

### 3. Duplicate events w Workflow

**Problem**: W `workflow/events/` istniały 4 pary zduplikowanych eventów:
- `WorkflowGraphNodeExecutionRequestedEvent` = `GraphNodeExecutionRequestedEvent`
- `WorkflowGraphNodeExecutionAdvancedEvent` = `GraphNodeExecutionAdvancedEvent`
- `WorkflowGraphNodeExecutionCompletedEvent` — bez pary, ale zbędny
- `WorkflowGraphNodeExecutionFailedEvent` — bez pary, ale zbędny

**Rozwiązanie**: Usunięto `WorkflowGraphNodeExecution*` warianty, zachowano `GraphNodeExecution*`.

### 4. Dodanie WorkflowStatus.FAILED

**Problem**: `WorkflowStatus` miał tylko `ACTIVE/COMPLETED/ABORTED`. `WorkflowFailedEvent` istniał, ale nie był nigdy emitowany — brakowało metody `fail()` i statusu `FAILED`.

**Rozwiązanie**:
- Dodano `FAILED = "failed"` do `WorkflowStatus`
- Dodano metodę `Workflow.fail(now, task_execution_id)`
- Dodano `PAUSED = "paused"` + metody `pause()/resume()` + eventy `WorkflowPausedEvent/WorkflowResumedEvent`

### 5. WorkflowStateInput/Output ID fix

**Problem**: `WorkflowStateInput.id` i `WorkflowStateOutput.id` były typu `WorkflowId` (ID agregatu właściciela), a nie dedykowanego typu.

**Rozwiązanie**: Dodano `WorkflowStateInputId` i `WorkflowStateOutputId` VOs, zaktualizowano encje.

### 6. GraphNodeExecution retry

**Problem**: Pole `retries` istniało w definicji, ale agregat nie miał metody `retry()`. Przejście `FAILED → PENDING` nie istniało.

**Rozwiązanie**:
- Dodano pole `_remaining_retries` (dekrementowane przy retry)
- Dodano metodę `retry(now)` → `FAILED → PENDING` + `GraphNodeExecutionRetriedEvent`
- Stan `PENDING` po retry pozwala na ponowne `start()`

### 7. Suspended w GraphExecution

**Problem**: Brak możliwości wstrzymania grafu.

**Rozwiązanie**:
- Dodano `GraphExecutionStatus.SUSPENDED`
- Metody `suspend(now)` (EXECUTING → SUSPENDED) i `resume(now)` (SUSPENDED → EXECUTING)
- `fail()` rozszerzone o możliwość fail z SUSPENDED

### 8. TaskExecution timeout

**Problem**: `TaskExecution` mógł wisieć w `IN_PROGRESS` bezterminowo.

**Rozwiązanie**:
- Dodano `TaskExecutionStatus.TIMED_OUT`
- Metoda `timeout(now)` → `IN_PROGRESS → TIMED_OUT` + `TaskExecutionTimedOutEvent`

### 9. Fix typo GraphExecutionRoutingService

**Problem**: Klasa nazywała się `GraphExcetutionRoutingService` (brak "u" w Execution).

**Rozwiązanie**: Przemianowano na `GraphExecutionRoutingService`, zaktualizowano API.

### 10. Fix EnvelopeLifecycleService.advance()

**Problem**: Metoda `advance()` nie robiła advance — tylko zwracała status.

**Rozwiązanie**: Przemianowano na `evaluate_status()`.

### 11. WorkflowTransitionService dla TransitionDefinition

**Problem**: Serwis używał starego entity `GraphNodeTransitionExecution` z `graph_execution/entities`.

**Rozwiązanie**: Zaktualizowano na `TransitionDefinition` + `GraphNodeTransitionExecution` aggregate.

---

## Stan obecny po zmianach

### Usunięte legacy
- `GraphExecution._state_inputs`, `_state_outputs` (były dublowane z oddzielnymi agregatami)
- `GraphExecution._loop_counters` (przeniesione do `GraphNodeTransitionExecution`)
- `GraphExecution._graph_definition_id`, `_timeout_at`, `_correlation_id`, `_tags`
- `GraphExecution._state_input` (dict), `_state_output` (dict)
- `GraphExecution.from_graph_definition()`
- `GraphExecution.increment_loop_counter()`
- `LoopCounter` VO (nieużywany, zastąpiony przez `GraphNodeTransitionExecution.current_iteration`)
- `WorkflowGraphNodeExecutionRequestedEvent`, `WorkflowGraphNodeExecutionAdvancedEvent`, `WorkflowGraphNodeExecutionCompletedEvent`, `WorkflowGraphNodeExecutionFailedEvent`
- Entity `graph_execution/entities/graph_node_transition_execution.py`
- Entity `graph_execution/entities/graph_execution_state_input.py` (dublowane z oddzielnym agregatem)
- Entity `graph_execution/entities/graph_execution_state_output.py` (dublowane z oddzielnym agregatem)
- `WorkflowStateInput.id` jako `WorkflowId` (zamienione na `WorkflowStateInputId`)
- `WorkflowStateOutput.id` jako `WorkflowId` (zamienione na `WorkflowStateOutputId`)
- `GraphExcetutionRoutingService` → `GraphExecutionRoutingService`
- `EnvelopeLifecycleService.advance()` → `evaluate_status()`

### Zachowane jako V3 (nie legacy)
- `GraphExecution._graph_node_execution_ids` — używane przez nawigatory
- `GraphExecution._transitions` — ale jako `list[TransitionDefinition]`
- `GraphExecution.graph_node_executions` — helper do nawigacji
- `GraphNodeExecution.position`, `mode`, `node_type` — używane przez infrastrukturę
- `TaskExecution.created_at`, `rename()`, `execute_in_workflow()`, `prepare_workspace()` — stare metody ale nie szkodzą

### Dodane nowe
- `TransitionDefinition` VO
- `GraphExecutionStatus.SUSPENDED`
- `WorkflowStatus.PAUSED`, `WorkflowStatus.FAILED`
- `TaskExecutionStatus.TIMED_OUT`
- `GraphNodeExecutionRetriedEvent`
- `TaskExecutionTimedOutEvent`
- `WorkflowPausedEvent`, `WorkflowResumedEvent`
- `Workflow.pause()`, `resume()`, `fail()`
- `GraphExecution.suspend()`, `resume()`
- `GraphNodeExecution.retry()`
- `TaskExecution.timeout()`
- `WorkflowStateInputId`, `WorkflowStateOutputId` VOs

---

## Rekomendacje — co jeszcze wymaga uwagi

### 1. State I/O — konsolidacja wykonana
Cztery osobne agregaty (`GraphExecutionStateInput`, `GraphExecutionStateOutput`, `TaskExecutionStateInput`, `TaskExecutionStateOutput`) zostały połączone w 2:
- `GraphExecutionState` — z polem `kind: StateKind.INPUT | StateKind.OUTPUT`
- `TaskExecutionState` — z polem `kind: StateKind.INPUT | StateKind.OUTPUT`

Eventy `GraphExecutionStateInputChangedEvent` i `GraphExecutionStateOutputChangedEvent` zostały połączone w `GraphExecutionStateChangedEvent` z polem `kind`.

Schemat bazy danych (tabele `graph_execution_state_input`, `graph_execution_state_output`, `task_execution_state_input`, `task_execution_state_output`) NIE został zmieniony — na razie istnieją 4 osobne tabele mapowane przez 2 agregaty. Docelowo można scalić w 2 tabele z kolumną `kind`.

### 2. State I/O — agregaty niespójne (DO ZROBIENIA PÓŹNIEJ)

Po konsolidacji GraphExecution i TaskExecution pozostały inne agregaty z własnymi state input/output, ale modelowane NIESPÓJNIE:

| Agregat | State Input | State Output | Aktualny model | Docelowy model |
|---------|-------------|--------------|----------------|----------------|
| **GraphExecution** | usunięte wewn. entity | usunięte wewn. entity | Osobny agregat `GraphExecutionState` z `kind` | ✅ OK |
| **TaskExecution** | usunięte wewn. entity | usunięte wewn. entity | Osobny agregat `TaskExecutionState` z `kind` | ✅ OK |
| **Workflow** | `WorkflowStateInput` entity | `WorkflowStateOutput` entity | Wewnętrzne entity wewnątrz Workflow | ❌ Należy wydzielić jako `WorkflowState` z `kind` |
| **Session** | `SessionStateInput` entity | `SessionStateOutput` entity | Wewnętrzne entity wewnątrz Session | ❌ Należy wydzielić jako `SessionState` z `kind` |
| **GraphNodeExecution** | `GraphNodeExecutionStateInput` entity | `GraphNodeExecutionStateOutput` entity | Wewnętrzne entity wewnątrz agregatu | ✅ OK — stan noda nie jest współdzielony z zewnątrz |

**Problem krytyczny**: `add_state_input()` i `add_state_output()` zostały usunięte z `GraphExecution` i `TaskExecution`, ale **13 handlerów aplikacyjnych** wciąż je wywołuje (m.in. `graph_execution_created_handler.py`, `graph_node_execution_completed_propagate_output_handler.py`, `propagate_*_to_*.py`).

**Co trzeba zrobić później**:
1. Przywrócić `add_state_input()`/`add_state_output()` w `GraphExecution` i `TaskExecution` jako delegację do `GraphExecutionState`/`TaskExecutionState` (z odpowiednim `kind`)
2. Stworzyć `WorkflowState` aggregate (analogicznie do `GraphExecutionState` z `kind`)
3. Stworzyć `SessionState` aggregate (analogicznie do `GraphExecutionState` z `kind`)
4. Dodać `WorkflowStateRepository` i `SessionStateRepository`
5. Zaktualizować 13 handlerów
6. Dodać eventy `WorkflowStateChangedEvent`, `SessionStateChangedEvent`

**Uwaga**: `User` i `Project` to inny bounded context — nie zmieniać.

### 2. SubGraphCompensation — martwy port
Port `SubGraphCompensation` istnieje (z `compensate()` i `on_child_failed()`), ale nie jest nigdy wywoływany. Wymaga implementacji sagi kompensacyjnej.

### 3. Session timeout
`Session` nie ma idle timeout. `SessionStatus` ma tylko `OPEN/CLOSED`. Warto dodać `Session.expire()` + `SessionExpiredEvent`.

### 4. Causation chain
`DomainEvent` ma pole `causation_id`, ale `AggregateRoot.append_event()` nie ustawia go automatycznie. Warto ustawiać `causation_id` z ID ostatniego eventu lub ID komendy.

### 5. WorkflowStateInput/Output — unused
Workflow ma metody `add_state_input()/add_state_output()` ale nie ma dedykowanych oddzielnych agregatów dla workflow state — w przeciwieństwie do GraphExecution i TaskExecution. To niespójność.

### 6. Testy do aktualizacji
- `test_graph_execution_counters.py` — usunięty (LoopCounter nieużywany)
- `test_transition_based_navigator.py` — zaktualizowany na TransitionDefinition
- `test_mappers_round_trip.py` — zaktualizowany na TransitionDefinition
- Pozostałe testy mogą wymagać weryfikacji przy pierwszym uruchomieniu

### 7. Mapper GraphExecution — pola domyślne
W mapperze `graph_execution_entity_to_model()` ustawiamy puste stringi dla usuniętych legacy pól (`graph_definition_id=""`, `state_input={}` itp.). Docelowo te kolumny w DB można usunąć lub oznaczyć jako nullable.

### 8. `_graph_node_execution_ids` — refaktoring przyszłości
Docelowo `GraphExecution` nie powinien trzymać listy ID node'ów — powinien delegować to do repozytorium `GraphNodeExecutionRepository` (jak robi to `TransitionBasedGraphNodeExecutionNavigator.first_async()`). Obecnie lista ID jest potrzebna nawigatorom synchronicznym (`graph_node_executions` property).
