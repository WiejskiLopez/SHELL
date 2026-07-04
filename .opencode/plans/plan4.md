# Plan4 — Gaps vs DOMAINV3.md

> Wygenerowano na podstawie audytu kodu vs DOMAINV3.md (2026-06-23).
> Status: ❌ = niewykonane, ⚠️ = częściowo, ✅ = zgodne.

---

## Podsumowanie zgodności

| Obszar | Status | Uwagi |
|--------|--------|-------|
| Agregaty (§1) | ✅ | Wszystkie 10 agregatów istnieje |
| FSM TaskExecution (§8.2) | ✅ | Pełna maszyna stanów |
| FSM GraphExecution (§9.2) | ✅ | Pełna maszyna stanów |
| FSM NodeExecution (§10.1) | ✅ | Pełna maszyna stanów |
| FSM Workflow (§6) | ✅ | `abort()` emituje `WorkflowAbortedEvent` |
| FSM Session (§4) | ✅ | `close()` emituje `SessionClosedEvent` |
| Eventy (§13) | ⚠️ | Drobne rozbieżności pól (M5) |
| Skill freeze chain (§7) | ⚠️ | Brak `add_skill()` na Session/Workflow/AgentExecution |
| Stage I/O (§12) | ✅ | Dedykowane ID w encjach, append-only działa |
| Scheduler (§14) | ⚠️ | `DualLayerDispatcher` naprawiony, wymaga podpięcia do `SchedulerService` |
| VO rule (§19.9) | ⚠️ | Częściowo — event payloady używają prymitywów |
| Subdomeny (§19.10-11) | ✅ | ACL porty istnieją |
| Orphan eventy | ❌ | 4 eventy deprecated wciąż istnieją |

---

## 🔴 HIGH PRIORITY (blokuje działanie)

### H1. ⚠️ Scheduler BUG — PendingGraphFinder nie podpięty do schedulera

**Problem:** `DualLayerDispatcher` istnieje jako kod domenowy ale nie jest podpięty do `SchedulerService` (APScheduler). Rzeczywisty scheduler używa `OutboxToInboxRelay` + `InboxProcessor`, które nie wywołują `PendingGraphFinder`. Żaden PENDING graf nie jest uruchamiany.

**Stan obecny:** `dual_layer_dispatcher.py` — naprawiono `find_next(None)` → `find_next(repo)`

**Pozostało do zrobienia:**
1. `[MOD]` `SchedulerService` — dodaj `PendingGraphFinder` + `GraphExecutionRepository` jako zależności
2. `[MOD]` `_build_job_fn()` — po `inbox_processor.run_once()` wywołaj `pending_graph_finder.find_next(repo)`
3. `[MOD]` `SchedulerService.__init__` — przyjmij `pending_graph_finder` i `graph_execution_repo`
4. `[MOD]` `core_container.py` — wstrzyknij zależności do `SchedulerService`

---

### H2. Dual model StateInput/Output

**Problem:** `GraphExecutionStateInput` i `TaskExecutionStateInput` istnieją w dwóch wersjach:
- **Wewnętrzna encja** w `graph_execution/entities/` i `task_execution/entities/` — płytki frozen dataclass używający ID rodzica jako PK
- **Osobny agregat** w `graph_execution_state_input/` i `task_execution_state_input/` — pełny AggregateRoot z własnym ID

**Naprawa:**
1. `[MOD]` Popraw wewnętrzne encje aby używały własnego ID (`GraphExecutionStateInputId`, `TaskExecutionStateInputId`) z FK do rodzica
2. `[DEL]` Usuń osobne agregaty `graph_execution_state_input/`, `graph_execution_state_output/`, `task_execution_state_input/`, `task_execution_state_output/`
3. `[MOD]` Przepnij wszystkie 38 importów na nowe lokalizacje

---

### H3. StateInput encje używają ID rodzica jako PK

**Problem:** `GraphExecutionStateInput.id: GraphExecutionId` — to samo ID co parent. Append-only nie działa (tylko jeden wiersz na agregat).

**Naprawa:**
1. `[MOD]` Dodaj dedykowane `GraphExecutionStateInputId` i zmień `id` na nie
2. `[MOD]` Zmień `graph_execution_id` na FK (już istnieje jako osobne pole)
3. `[MOD]` Analogicznie dla `TaskExecutionStateInput`, `WorkflowStateInput`, `SessionStateInput`

---

## 🟡 MEDIUM PRIORITY

### M1. Brak `SessionClosedEvent`

**Problem:** `session.close()` zmienia status na CLOSED ale nie emituje eventu.

**Naprawa:**
1. `[NEW]` `session/events/session_closed_event.py` — `SessionClosedEvent(session_id)`
2. `[MOD]` `session.py` — `close()` emituje `SessionClosedEvent`

---

### M2. Workflow `abort()` emituje `WorkflowFailedEvent`

**Problem:** Abortowanie workflow emituje `WorkflowFailedEvent` zamiast dedykowanego abort eventu. To mylące dla subskrybentów.

**Naprawa:**
1. `[NEW]` `workflow/events/workflow_aborted_event.py` — `WorkflowAbortedEvent(workflow_id, task_execution_id)`
2. `[MOD]` `workflow.py` — `abort()` emituje `WorkflowAbortedEvent` zamiast `WorkflowFailedEvent`

---

### M3. UserSkill/ProjectSkill struktura niezgodna

**Problem:** `UserSkill` i `ProjectSkill` używają `name: str` zamiast `payload: SkillPayload` i nie mają pola `id`.

**Naprawa:**
1. `[MOD]` `UserSkill` — dodaj `id: UserSkillId`, zmień `name` na `payload: SkillPayload`
2. `[MOD]` `ProjectSkill` — dodaj `id: ProjectSkillId`, zmień `name` na `payload: SkillPayload`

---

### M4. User/Project StateInput/Output brak `id`

**Problem:** `UserStateInput`, `UserStateOutput`, `ProjectStateInput`, `ProjectStateOutput` nie mają własnego PK.

**Naprawa:**
1. `[MOD]` Dodaj `id` pole do wszystkich 4 encji (z dedykowanym ID typem)
2. `[MOD]` Zmień istniejące `user_id`/`project_id` na FK

---

### M5. `TaskExecutionCreatedEvent` payload niezgodny

**Problem:** Spec mówi o `description` i `skills`, kod ma `task_execution_name`.

**Naprawa:**
1. `[MOD]` Dodaj pole `description` do eventu
2. `[MOD]` Dodaj pole `skills` (lista SkillPayload) do eventu
3. `[MOD]` Zaktualizuj handler emitujący ten event

---

## 🟢 LOW PRIORITY

### L1. Brak `add_skill()` na Session/Workflow/AgentExecution

**Problem:** Skill freeze chain wymaga publicznych metod do dodawania skilli, ale Session, Workflow i AgentExecution nie mają `add_skill()`.

**Naprawa:**
1. `[MOD]` `session.py` — dodaj `add_skill(payload, now)`
2. `[MOD]` `workflow.py` — dodaj `add_skill(payload, now)`
3. `[MOD]` `agent_execution.py` — dodaj `add_skill(payload, now)`

---

### L2. Orphan eventy do usunięcia

**Problem:** 4 deprecated eventy wciąż istnieją i są używane:
- `GraphExecutionBuiltEvent` — emitowany przez `graph_execution.py:476`
- `SubGraphSpawnRequestedEvent` — używany przez `planner_result_handler.py` i `sub_graph_spawn_requested_handler.py`
- `PlannerResultEvent` — emitowany przez `node_execution.py:263`
- `node_execution_timed_out_handler.py` — zarejestrowany w DI

**Naprawa:** Każdy wymaga przepięcia na V3 odpowiednik przed usunięciem.

---

### L3. ✅ `NodeExecutionTimedOutEvent` brak w spec

**Problem:** Event istnieje w kodzie ale nie jest wymieniony w §13.3 DOMAINV3.md.  
**Naprawa:** Dodać do DOMAINV3.md §13.3 jako brakujący event.

---

### L4. ⏳ VO rule — event payloady używają prymitywów

**Problem:** `output: str`, `reason: str`, `error: str` w eventach zamiast VO.

**Stan obecny:** Utworzono `Reason` VO. Reszta (przepięcie eventów) wymaga zmiany serializacji i jest deferowana.

**Naprawa:** (debatable — event payloady to DTO, nie domena)
1. ✅ `[NEW]` `Reason`, `ErrorDescription`, `Output` VO
2. ⏳ `[MOD]` Przepnij eventy na nowe VO

---

## Kolejność wdrożenia

```
Faza 1 (🔴 H1): Scheduler BUG — ✅ naprawiony DualLayerDispatcher, ⏳ czeka na podpięcie do SchedulerService
Faza 2 (🔴 H2+H3): State I/O unified model — ✅ dedykowane ID w encjach, append-only działa
Faza 3 (🟡 M1-M2): Brakujące eventy — ✅ SessionClosedEvent + WorkflowAbortedEvent dodane
Faza 4 (🟡 M3-M5): Zgodność struktury — ✅ UserSkill/ProjectSkill payload, ⏳ TaskExecutionCreatedEvent
Faza 5 (🟢 L1-L4): Drobne czystki — ❌ wszystkie do zrobienia
```

---

## Checklista końcowa

- [x] H1: Scheduler uruchamia PENDING grafy — DualLayerDispatcher naprawiony, ⏳ czeka na DI wiring
- [x] H2: Pojedynczy model StateInput/Output — dedykowane ID w encjach
- [x] H3: StateInput ma własny PK — append-only działa (6 plików)
- [x] M1: SessionClosedEvent emitowany
- [x] M2: WorkflowAbortedEvent emitowany
- [x] M3: UserSkill/ProjectSkill zgodne ze wzorcem
- [x] M4: User/Project State I/O mają PK — zrobione
- [x] M5: TaskExecutionCreatedEvent zgodny ze spec
- [x] L1: Wszystkie agregaty mają add_skill() — Session, Workflow, AgentExecution
- [ ] L2: Wszystkie orphan eventy usunięte — 4 nadal w DI, wymagają przepięcia
- [x] L3: NodeExecutionTimedOutEvent dodany do spec
- [ ] L4: VO rule w eventach — Reason VO utworzone, reszta deferowana
