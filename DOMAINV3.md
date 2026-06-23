# Domain Architecture v3 — SHELL

> **Cel:** czysty, enterprise-grade flow oparty na opisie funkcjonalnym i zasadach enterprise (DDD + Event-Driven + CQRS-read).
>
> **Zasada redakcyjna:** tylko to, co musi istnieć, by maszyneria ruszyła. Encje, agregaty, eventy, maszyny stanów, reguły. Bez opisów implementacji infrastruktury.

---

## 0. Decyzje architektoniczne (rozstrzygnięcia rozdźwięków)

Zanim opiszę model, фиксuję kluczowe decyzje architektoniczne.

| # | Wymaganie | Decyzja | Uzasadnienie (enterprise) |
|---|-----------|-----------|---------------------------|
| **D1** | Opis: *"wszystkie nody mają skille"*. | **Skille są wszędzie**: User, Project, Session, Workflow, TaskExecution, GraphExecution, AgentExecution. Każdy poziom może je **dziedziczyć i rozszerzać**. | Opis definiuje kontrakt domenowy. Spójny model dziedziczenia skilli = jeden mechanizm freeze-and-snapshot na wszystkich poziomach. |
| **D2** | Opis: *"krawędzie podejmują decyzje, edge emituje eventy decyzyjne; node emituje komunikacyjne"*. | **Dualna odpowiedzialność**: Node emituje `*NodeExecution*Event` (co się stało, jaki result). Edge emituje `*Transition*Event` (jaka decyzja routingowa, co dalej). Node NIE decyduje o routing — to Edge. | Single Responsibility. Node = "wykonałem pracę", Edge = "zdecydowałem o przepływie". |
| **D3** | Opis: *"eventy komunikacyjne zawsze obsługiwane przed decyzyjnymi — decyzja wymaga poprawnych danych"*. | **Kolejka dwuwarstwowa**: warstwa komunikacyjna (state changes) jest przetwarzana pierwsza; warstwa decyzyjna (routing) jest ewaluowana gdy inbox komunikacyjny dla danego noda jest pusty. | Eventualna konsystencja z gwarancją: decyzja nigdy na nieświeżych danych. |
| **D4** | Opis: *"input/output stage na każdym poziomie (node, graph, task, workflow, session, user, project)"*. | **Stage I/O wszędzie, jako osobne tabele per agregat**: każdy agregat ma własne `*StateInput` (dostaje) i `*StateOutput` (generuje) z FK do roota — bez polimorficznego dyskryminatora. Reguła propagacji: output dziecka → input rodzica. | Jednolity kontrakt danych, pełna integralność referencyjna (FK+CASCADE), symetrycznie do wzorca `*Skill`. |
| **D5** | Zagnieżdżone sub-grafy rekurencyjne + rekursywne `SubGraphSettledEvent`. | Zachowane, ale z **jawnym limitem `max_subgraph_depth`** i zakazem samozawołań cyklicznych między grafami. | Ochrona przed nieskończoną rekurencją. |
| **D6** | Dylemat: PARALLEL jako współbieżne nody wewnątrz grafu vs Sub-graf. | **Brak PARALLEL/JOIN**. Graf to pipeline sekwencyjny — nodów w grafie nie dodaje się dynamicznie; definiuje je PLANNER w fazie planowania. Współbieżność i podział pracy = **wyłącznie** spawn 1..N sub-grafów. | Jeden mechanizm współbieżności (sub-grafy); każda jednostka ma pełny cykl życiowy, własną weryfikację i własny stan. |
| **D7** | Replan jako nowy GraphExecution z `parent=None` + `current_cycle` na TaskExecution. | Zachowane. **Kluczowe**: jedynym ogranicznikiem replanu jest `max_planning_cycles`. Każdy FAILED rundy głównej → replan. | Brak flagi "replanowalności" = mniej stanu ukrytego. |
| **D8** | Opis: *"Workflow zbiera podsumowania tasków, mogą być wejściem do kolejnego tasku"*. | **Workflow ma własny `WorkflowStateOutput`** = agregat podsumowań zakończonych tasków. | Workflow jest realnym agregatem zbierającym artefakty, nie tylko kontenerem. |
| **D9** | GraphExecution wymaga własnych skili. | **GraphExecution ma własne skille** (dziedziczone z TaskExecution + rozszerzenia od PLANNERA). | Spójność z D1 — każdy poziom executionowy ma skille. |
| **D10** | User/Project wymagają własnych agregatów persistentnych. | **`User` i `Project` jako agregaty persistentne** (poza sesją), z własnymi skillami i state. Session tylko snapshotuje ich skille. | Źródło prawdy o userze/projekcie żyje poza sesją; Session jest zamrożonym snapshotem wykonania. |

---

## 1. Przegląd agregatów

| Agregat (root) | Odpowiedzialność | Kluczowe ID |
|----------------|-----------------|-------------|
| **User** | Tożsamość i preferencje użytkownika (persistent, poza sesją). | `user_id` |
| **Project** | Definicja projektu (persistent, poza sesją). | `project_id` |
| **Session** | Zamrożony snapshot: user, project, środowisko (windows/docker/...). Root wykonania. | `session_id` |
| **AgentConfigExecution** | Konfiguracja LLM dla sesji (UNIQUE na session). Źródło configu dla każdego noda LLM. | `agent_config_execution_id` → `session_id` |
| **Workflow** | Linia produkcyjna zadań. Zna architekturę/wymagania. Agreguje podsumowania tasków. | `workflow_id` → `session_id` |
| **TaskExecution** | Jedno kompletne zadanie. Cel, limit rund, aktualna runda. | `task_execution_id` → `workflow_id` |
| **GraphExecution** | Jedna runda (plan→exec→verify). `parent=None` → runda główna; `parent=<id>` → sub-graf. | `graph_execution_id` → `task_execution_id` |
| **GraphNodeExecution** | Jeden krok w rundzie. Role: PLANNER, AGENT, TOOLS, VERIFIER (+ dowolna rola agentowa). | `graph_node_execution_id` → `graph_execution_id` |
| **GraphNodeTransitionExecution** | **Krawędź grafu** = strategia decyzyjna. Emituje eventy routingowe. | `transition_execution_id` → (source_node, target_node) |
| **AgentExecution** | Znacznik "ten node był agentem". Agreguje skille użyte przy wykonaniu. | `agent_execution_id` → `graph_node_execution_id` |

**Wzorzec konsekwentny (skills + state):** Każdy agregat ma **własne tabele** `*Skill` oraz `*StateInput` / `*StateOutput` (z FK do swojego roota, bez polimorficznego dyskryminatora):

| Agregat | Tabela skili | Tabela wejścia | Tabela wyjścia |
|---------|--------------|----------------|----------------|
| User | `UserSkill` | `UserStateInput` | `UserStateOutput` |
| Project | `ProjectSkill` | `ProjectStateInput` | `ProjectStateOutput` |
| Session | `SessionSkill` | `SessionStateInput` | `SessionStateOutput` |
| Workflow | `WorkflowSkill` | `WorkflowStateInput` | `WorkflowStateOutput` |
| TaskExecution | `TaskExecutionSkill` | `TaskExecutionStateInput` | `TaskExecutionStateOutput` |
| GraphExecution | `GraphExecutionSkill` | `GraphExecutionStateInput` | `GraphExecutionStateOutput` |
| GraphNodeExecution | — (skille przez `AgentSkillExecution`) | `GraphNodeExecutionStateInput` | `GraphNodeExecutionStateOutput` |
| AgentExecution | `AgentSkillExecution` | — | — |

Brak polimorficznego `owner_type` — każda tabela ma bezpośredni FK do swojego agregatu. To eliminuje błędy referencji i upraszcza query/indexy (symetrycznie do istniejącego wzorca skilli).

---

## 2. Hierarchia i relacje

```
User / Project  (persistentne agregaty kontekstowe, poza sesją)
    │
    ▼  (skille + state zamrażane w momencie otwarcia sesji)
Session
 ├── AgentConfigExecution (session_id, UNIQUE)        # config LLM dla sesji
 ├── SessionStateInput[] / SessionStateOutput[]
 └── Workflow (session_id)
      ├── WorkflowStateInput[] / WorkflowStateOutput[]    # podsumowania tasków
      └── TaskExecution (workflow_id)
           ├── TaskExecutionSkill[] (frozen snapshot)
           ├── TaskExecutionStateInput[] / TaskExecutionStateOutput[]
           │
           ├── GraphExecution (runda #1, parent=None) ──▶ inkrementuje current_cycle
           │    ├── GraphExecutionSkill[] (dziedziczone + rozszerzone)
           │    ├── GraphExecutionStateInput[] / GraphExecutionStateOutput[]
           │    ├── GraphNodeExecution: PLANNER
           │    ├── GraphNodeExecution: AGENT ─┬─ AgentExecution
           │    │                              └─ AgentSkillExecution[]
           │    ├── GraphNodeExecution: TOOLS
           │    │   └── GraphNodeExecutionStateInput[] / GraphNodeExecutionStateOutput[] (per node)
           │    ├── GraphNodeExecution: VERIFIER
           │    └── GraphNodeTransitionExecution[] (krawędzie, w tym SEQUENCE auto)
           │
           ├── GraphExecution (sub-graf, parent=<id>)  ──▶ NIE inkrementuje cycle
           │    └── ... (ten sam kształt co graf główny)
           │
           └── GraphExecution (runda #2, parent=None, state_input.previous_attempt_id=<failed>)
```

### 2.1 Reguła `parent_graph_execution_id`

| Wartość | Znaczenie | Inkrementuje `current_cycle`? |
|---------|-----------|------------------------------|
| `None` | Graf główny rundy (pierwsza runda LUB replan). | **TAK** |
| `<GraphExecutionId>` | Sub-graf spawnnięty przez PLANNERA wskazanego parenta. | **NIE** |

- Relacja **jednokierunkowa**: child zna parenta. Parent NIE trzyma listy dzieci — query po `parent_graph_execution_id`.
- **Replan = nowy graf główny** (`parent=None`); link do failed poprzednika w `GraphExecutionStateInput.previous_attempt_id` (dane audytowe, nie relacja).
- **Sub-graf NIE replanuje wewnętrznie** — failure bubluje do parent PLANNER (§8.3).

### 2.2 Reguła propagacji Stage I/O (D4)

```
GraphNodeExecutionStateOutput       →  GraphExecutionStateInput    # node generuje → graf to otrzymał
GraphExecutionStateOutput  →  TaskExecutionStateInput     # (przez GraphExecutionCompletedEvent)
GraphExecutionStateOutput(child) → GraphExecutionStateInput(parent)  # (przez SubGraphSettledEvent)
TaskExecutionStateOutput   →  WorkflowStateInput          # (przez TaskExecutionCompletedEvent)
WorkflowStateOutput        →  TaskExecutionStateInput     # wejście kolejnego tasku
SessionStateOutput         →  WorkflowStateInput          # (kontekst startu workflow)
```

Każdy poziom ma append-only log `*StateInput` i `*StateOutput`. Propagacja przez handlery eventowe.

---

## 3. User i Project — persistentny kontekst (poza sesją)

`User` i `Project` to agregaty **persistentne** — żyją poza sesją, modyfikowalne w czasie. `Session` tylko je **snapshotuje** w momencie otwarcia.

```
User
 ├── id: UserId
 ├── identity: {...}                      # auth, profil
 ├── UserSkill[]                          # preferencje, historia, zasady usera
 ├── UserStateInput[] / UserStateOutput[]   # wejście/wyjście cyklu życia usera (np. onboarding)
 └── status: ACTIVE | DISABLED

Project
 ├── id: ProjectId
 ├── name, repo_url, ...
 ├── ProjectSkill[]                         # konwencje, toolchain, CI/CD projektu
 ├── ProjectStateInput[] / ProjectStateOutput[]
 └── status: ACTIVE | ARCHIVED
```

- To są **źródła prawdy** o userze i projekcie. `Session` zamraża ich skille do `SessionSkill` przy starcie (§4.1).
- Nie są częścią drzewa wykonania (session→workflow→...), ale są **źródłem dziedziczenia** skilli i kontekstu.

---

## 4. Session — zamrożony snapshot kontekstu

```
Session
 ├── id: SessionId
 ├── user_id: UserId                       # FK → User (referencja, nie kopia)
 ├── project_id: ProjectId                 # FK → Project (referencja, nie kopia)
 ├── environment: {os, runtime, ...}       # windows / docker / ... (snapshot)
 ├── status: OPEN | CLOSED
 ├── opened_at, closed_at
 ├── SessionStateInput[]                   # co sesja otrzymała (append-only)
 └── SessionStateOutput[]                  # artefakty sesji (append-only)
```

- Skille usera i projektu są **zamrażane** w momencie otwarcia sesji (kopia do `SessionSkill`; append-only do zamknięcia).
- Session **nie jest chatem** — nie przechowuje wiadomości użytkownika.
- `user_id`/`project_id` to referencje do żywych agregatów; tylko skille są kopiowane (freeze).
- Workflow dziedziczy skille z Session i może je rozszerzać.

### 4.1 Tabele skilli i state sesji

```
SessionSkill
 ├── id, session_id (FK CASCADE)
 ├── payload: JSON
 └── created_at

SessionStateInput
 ├── id, session_id (FK CASCADE)
 ├── payload: JSON
 └── created_at

SessionStateOutput
 ├── id, session_id (FK CASCADE)
 ├── payload: JSON
 └── created_at
```

---

## 5. AgentConfigExecution — config LLM sesji

```
AgentConfigExecution
 ├── id
 ├── session_id (FK, UNIQUE)              # max 1 rekord na sesję (CONSTRAINT na bazie)
 ├── config: Config                       # VO — opakowanie dict (model, temperature, max_tokens, top_p, ...)
 └── created_at, updated_at
```

- Źródło configu dla **wszystkich nodów LLM** (PLANNER i AGENT).
- Pierwszy zapis = INSERT; kolejne = UPDATE (jeden aktualny config, nie append-only).
- Brak rekordu → config domyślny z kodu (zalecane).

---

## 6. Workflow — linia produkcyjna + agregat artefaktów

```
Workflow
 ├── id, session_id
 ├── status: ACTIVE | COMPLETED | ABORTED
 ├── WorkflowSkill[]
 ├── WorkflowStateInput[]                  # cel/kontekst workflow (append-only)
 └── WorkflowStateOutput[]                 # AGREGAT: podsumowania zakończonych tasków
```

- Wszystkie reguły/zasady/wymagania są **skillami** (JSON), nie polami na Workflow.
- `WorkflowStateOutput` gromadzi wyniki tasków i może być wejściem kolejnego tasku.

```
WorkflowSkill
 ├── id, workflow_id (FK CASCADE)
 ├── payload: JSON
 └── created_at

WorkflowStateInput
 ├── id, workflow_id (FK CASCADE)
 ├── payload: JSON
 └── created_at

WorkflowStateOutput
 ├── id, workflow_id (FK CASCADE)
 ├── payload: JSON
 └── created_at
```

---

## 7. Przepływ skilli (dziedziczenie + freeze)

```
User / Project (persistentne skille)
    │
    ▼  (FREEZE w momencie otwarcia sesji → SessionSkill)
Session (user, project, env skills)
    │
    ▼  (dziedziczenie + rozszerzenie)
Workflow (project, architecture, requirement skills)
    │
    ▼  (FREEZE w momencie tworzenia TaskExecution → TaskExecutionSkill)
TaskExecution
    │
    ▼  (dziedziczenie + rozszerzenie od PLANNERA → GraphExecutionSkill)
GraphExecution
    │
    ▼  (subset wybrany przez PLANNERA → AgentSkillExecution)
AgentExecution  (append-only ARCHIVE — co agent faktycznie dostał)
```

**Reguły:**
- **Freeze** = kopia skili z poziomu nadrzędnego, w momencie utworzenia podrzędnego. Po freeze zmiany wyższego poziomu nie wpływają na ten obiekt.
- **Archive** = `AgentSkillExecution` zapisywany w momencie uruchomienia agenta — dokładnie to, co dostał (audytowalność).

```
TaskExecutionSkill
 ├── id, task_execution_id (FK CASCADE)
 ├── payload: JSON
 └── created_at

GraphExecutionSkill
 ├── id, graph_execution_id (FK CASCADE)
 ├── payload: JSON
 └── created_at
```

---

## 8. TaskExecution — cykl życia zadania

### 8.1 Pola

```
TaskExecution
 ├── id, workflow_id
 ├── name, description                    # cel zadania (z pierwszego TaskExecutionStateInput)
 ├── max_planning_cycles: int             # limit rund głównych
 ├── current_cycle: int                   # liczba rozpoczętych rund głównych
 ├── status: CREATED | IN_PROGRESS | COMPLETED | FAILED | EXHAUSTED
 ├── work_dir: str
 ├── TaskExecutionSkill[]                 # frozen snapshot skili (Session+Workflow)
 ├── TaskExecutionStateInput[]            # append-only log wejść
 └── TaskExecutionStateOutput[]           # append-only log wyjść
```

```
TaskExecutionStateInput
 ├── id, task_execution_id (FK CASCADE)
 ├── payload: JSON
 └── created_at

TaskExecutionStateOutput
 ├── id, task_execution_id (FK CASCADE)
 ├── payload: JSON
 └── created_at
```

### 8.2 Maszyna stanów

```
[CREATED] ──TaskExecutionStartedEvent──▶ [IN_PROGRESS]
                                              │
                              ┌───────────────┼───────────────┐
                              │               │               │
                  TaskExecutionCompleted  TaskExecutionFailed  TaskExecutionExhausted
                              │               │               │
                         [COMPLETED]      [FAILED]       [EXHAUSTED]
```

- `CREATED → IN_PROGRESS`: gdy tworzony jest pierwszy `GraphExecution` rundy głównej (trigger: `GraphExecutionCreatedEvent` z `parent=None`).
- `IN_PROGRESS → COMPLETED`: główny `GraphExecution` bieżącej rundy → `COMPLETED`.
- `IN_PROGRESS → FAILED`: nieodwracalny błąd (np. verifier uznał niereplanowalny).
- `IN_PROGRESS → EXHAUSTED`: `current_cycle >= max_planning_cycles` przy próbie kolejnego replanu.
- Stany końcowe (`COMPLETED`, `FAILED`, `EXHAUSTED`) są **nierewersybilne**.

### 8.3 Reguły `current_cycle`

- Start: **0** przy `CREATED`.
- Każdy graf z `parent=None` inkrementuje `current_cycle` w momencie utworzenia:
  - Pierwszy graf → `current_cycle = 1`.
  - Replan → `current_cycle = 2`. Itd.
- Sub-grafy (`parent=<id>`) **NIE inkrementują**.
- Dopuszczalne rundy główne: `1..max_planning_cycles`. Próba `current_cycle+1 > max` → `EXHAUSTED` (zamiast tworzenia grafa).

---

## 9. GraphExecution — cykl życia jednej rundy

### 9.1 Pola

```
GraphExecution
 ├── id, task_execution_id
 ├── parent_graph_execution_id: GraphExecutionId | None
 ├── depth: int                           # głębokość zagnieżdżenia sub-grafów (root=0)
 ├── status: PENDING | PLANNING | EXECUTING | VERIFYING | COMPLETED | FAILED
 ├── max_subgraph_depth: int              # limit rekurencji sub-grafów (D5)
 ├── GraphExecutionSkill[]
 ├── GraphExecutionStateInput[]           # goal, previous_attempt_id, children_results
 └── GraphExecutionStateOutput[]          # verifier_result, wyniki pośrednie
```

```
GraphExecutionStateInput
 ├── id, graph_execution_id (FK CASCADE)
 ├── payload: JSON                        # {goal, previous_attempt_id?, children_results?}
 └── created_at

GraphExecutionStateOutput
 ├── id, graph_execution_id (FK CASCADE)
 ├── payload: JSON                        # {verifier_result, intermediate_results}
 └── created_at
```

- Graf **NIE** przechowuje listy nodów ani listy dzieci. Oba znajduje się query'm.
- `depth` liczone od parenta; `depth > max_subgraph_depth` → `GraphExecutionFailedEvent`.

### 9.2 Maszyna stanów

```
[PENDING] ─GraphPlanningStartedEvent─▶ [PLANNING]
                                            │
                              ┌─────────────┴─────────────┐
                              │                           │
                  GraphSpawnedEvent              GraphPlannedEvent
                  (spawn sub-grafu)              (koniec planowania)
                              │                           │
                              ▼                           ▼
              [PLANNING] (utrzymane —               [EXECUTING]
               parent ma niezakonczone
               dzieci; scheduler
               nie rusza nodów parenta)
                              │
                  SubGraphSettledEvent
                  (wszystkie dzieci OK/FAIL)
                              │
                              ▼
               PLANNER wznowiony z wynikami
               sub-grafów w state_input
                              │
                              ▼
                         [EXECUTING]
                                            │
                                NodeCompleted/Failed
                                            │
                                            ▼
                                       [VERIFYING]
                                            │
                                  ┌─────────┴─────────┐
                                  │                   │
                       GraphExecutionCompleted   GraphExecutionFailed
                                  │                   │
                             [COMPLETED]           [FAILED]
```

**"Parent czeka na sub-grafy" NIE jest osobnym stanem.** Parent pozostaje w `PLANNING`. Scheduler wykrywa zajętość query'm: istnieją GraphExecution z `parent_graph_execution_id = parent.id` w stanie ≠ końcowym → parent ma niezakonczone dzieci → scheduler nie rusza jego nodów. `SubGraphSettledEvent` jest sygnałem wznowienia.

**Stany końcowe `COMPLETED`, `FAILED` są nierewersybilne.** Replan to **nowy** `GraphExecution` z `parent=None`, nie reset stanu.

### 9.3 Kiedy PLANNER spawnuje sub-graf

| Scenariusz | Opis |
|------------|------|
| **Podział zadania** | PLANNER dzieli zadanie → każdy pod-zadanie = osobny sub-graf z `payload.goal`. Sub-grafy **równoległe i niezależne**. |
| **Specjalistyczne zadanie** | Sub-graf ze specyficznymi skilami/rolą agentową dla konkretnego grafu. |
| **Human in the loop** | Sub-graf ze skillem `ask_user`. Wynik wraca do PLANNERA parenta. |
| **Dodatkowa analiza** | "Przeszukaj dokumentację", "przeanalizuj moduł X". |

---

## 10. GraphNodeExecution — krok + krawędzie

### 10.1 Pola

```
GraphNodeExecution
 ├── id, graph_execution_id
 ├── role: PLANNER | AGENT | TOOLS | VERIFIER | <custom agent role>
 ├── order: int                           # domyślna kolejność liniowa
 ├── status: PENDING | RUNNING | COMPLETED | FAILED | TIMED_OUT
 ├── GraphNodeExecutionStateInput[]                # co node dostał (append-only)
 └── GraphNodeExecutionStateOutput[]               # co node wygenerował (append-only)
```

```
GraphNodeExecutionStateInput
 ├── id, graph_node_execution_id (FK CASCADE)
 ├── payload: JSON
 └── created_at

GraphNodeExecutionStateOutput
 ├── id, graph_node_execution_id (FK CASCADE)
 ├── payload: JSON                        # result noda
 └── created_at
```

- Jeśli `role=AGENT` → powiązany `AgentExecution`.
- **Node NIE decyduje o routing** (D2). Node emituje eventy komunikacyjne (co zrobiłem, jaki result). Routing jest domeną **Edge** (§11).
- `result` noda = `payload` najnowszego wiersza `GraphNodeExecutionStateOutput`. Brak duplikacji pola na encji noda — output żyje w swojej tabeli.

### 10.2 Domyślny pipeline (liniowy)

```
PLANNER (0) → AGENT (1, opc.) → TOOLS (2, opc.) → VERIFIER (3)
```

- PLANNER i VERIFIER **obowiązkowe**; AGENT i TOOLS opcjonalne.
- Domyślna kolejność liniowa jest automatycznie modelowana jako krawędzie `SEQUENCE` między kolejnymi nodami (szczególny przypadek §11).

### 10.3 AgentExecution + AgentSkillExecution

```
AgentExecution
 ├── id, graph_node_execution_id
 └── config_snapshot: Config               # kopia configu z AgentConfigExecution (audyt)

AgentSkillExecution
 ├── id, agent_execution_id
 ├── payload: JSON
 └── created_at
```

- `AgentExecution` = znacznik "ten node był agentem" + archiwum skili tego wykonania.
- Config LLM pobierany z `AgentConfigExecution` (przez łańcuch FK aż do session). Snapshot zapisany dla audytu.

---

## 11. GraphNodeTransitionExecution — Edge jako strategia decyzyjna (D2, D6)

**To jest serce opisu funkcjonalnego.** Edge = strategia "co dalej". Edge **emituje eventy decyzyjne**; Node emituje eventy komunikacyjne.

### 11.1 Encja

```
GraphNodeTransitionExecution
 ├── id, graph_execution_id
 ├── source_node_execution_id
 ├── target_node_execution_id | spawn_spec            # target LUB definicja spawnu sub-grafu
 ├── edge_type: SEQUENCE | CONDITIONAL | LOOP
 │            | SPAWN_SUBGRAPH | ERROR_HANDLER | TIMEOUT | DEFAULT
 ├── condition_expression: str | None                 # dla CONDITIONAL
 ├── max_iterations: int | None                        # dla LOOP
 └── status: EVALUATED | TAKEN | SKIPPED
```

### 11.2 Typy krawędzi

| Typ | Kto decyduje | Zachowanie | Event decyzyjny |
|-----|--------------|-----------|-----------------|
| **SEQUENCE** | Automat | Następny node wg `order`. | `TransitionTakenEvent` |
| **CONDITIONAL** | Edge (na wyniku source noda) | Ewaluacja `condition_expression` na `result`; różne targety dla true/false. | `TransitionConditionEvaluatedEvent` → `TransitionTakenEvent` |
| **LOOP** | PLANNER / Edge | Powrót do source noda z enriched `state_input`; limit `max_iterations`. | `TransitionLoopedEvent` |
| **SPAWN_SUBGRAPH** | PLANNER | Tworzy nowy `GraphExecution` z `parent=<this>`. Parent czeka (§9.2). To **jedyne** narzędzie współbieżności i podziału pracy — PLANNER może w jednym kroku spawnąć 1..N sub-grafów. | `GraphSpawnedEvent` |
| **ERROR_HANDLER** | Scheduler (po FAILED noda) | Przekierowanie do noda obsługi błędów; brak → `GraphExecutionFailedEvent`. | `TransitionErrorHandledEvent` |
| **TIMEOUT** | Scheduler | Przekierowanie po timeout noda. | `TransitionTimedOutEvent` |
| **DEFAULT** | Fallback | Gdy żaden CONDITIONAL nie pasuje. | `TransitionTakenEvent` |

> **Brak PARALLEL/JOIN (D6).** Graf jest pipeline'em sekwencyjnym. Zbiór nodów ustala PLANNER w fazie planowania — nie dodaje się ich dynamicznie w trakcie wykonania. Współbieżność i podział pracy realizuje się **wyłącznie** przez `SPAWN_SUBGRAPH` (1..N sub-grafów). Dzięki temu każda jednostka współbieżna to pełny `GraphExecution` z własnym cyklem życiowym, własną weryfikacją i własnym stanem — zamiast surowych nodów sklejonych barierą synchronizacji.

### 11.3 Przepływ decyzyjny Edge'a

```
GraphNodeExecution → COMPLETED/FAILED/TIMED_OUT
    │
    ▼
Scheduler pobiera outgoing transitions dla noda
    │
    ├── Brak tranzycji → koniec pipeline (VERIFIER → GraphExecutionCompletedEvent)
    ├── SEQUENCE        → uruchom następny node wg order
    ├── CONDITIONAL     → ewaluuj warunek na result → wybierz target → TransitionTakenEvent
    ├── LOOP            → jeśli iteracje < max → wróć do source; inaczej → VERIFIER/FAILED
    ├── SPAWN_SUBGRAPH  → emit GraphSpawnedEvent → nowy GraphExecution(parent=this)
    │                     (1..N sub-grafów; parent zostaje w PLANNING aż wszystkie się skończą)
    ├── ERROR_HANDLER   → (przy FAILED) przekieruj do handlera
    ├── TIMEOUT         → (przy TIMED_OUT) przekieruj do handlera
    └── DEFAULT         → fallback
```

### 11.4 Podział pracy = sub-grafy (jeden mechanizm)

Współbieżność, fan-out, specjalizacja i human-in-the-loop realizuje się **wyłącznie** przez `SPAWN_SUBGRAPH`. Nie ma równoległych nodów wewnątrz grafa.

| Scenariusz | Jak działa przez sub-grafy |
|------------|----------------------------|
| **Fan-out (podział na pod-zadania)** | PLANNER spawnuje N sub-grafów z tym samym `parent_graph_execution_id`; scheduler uruchamia je współbieżnie; `SubGraphSettledEvent` zbiera wyniki po ostatnim. |
| **Zadanie specjalistyczne** | Sub-graf z własnym zestawem skilli (§7) i rolą agentową. |
| **Human-in-the-loop** | Sub-graf ze skillem `ask_user`; wynik wraca przez `SubGraphSettledEvent`. |
| **Re-spawn po porażce** | Nowy sub-graf z tym samym parentem, poprawionym `goal` (§15.3). |

---

## 12. Stage I/O — osobne tabele per agregat (D4)

Każdy agregat ma **własne tabele** `*StateInput` i `*StateOutput` (symetrycznie do wzorca `*Skill`). Brak polimorficznego dyskryminatora `owner_type` — każda tabela ma bezpośredni FK do swojego roota.

**Wspólny kształt (instancjonowany per agregat):**

```
<Agregat>StateInput                        # co agregat DOSTAŁ
 ├── id, <agregat>_id (FK CASCADE)
 ├── payload: JSON
 └── created_at

<Agregat>StateOutput                       # co agregat WYGENEROWAŁ
 ├── id, <agregat>_id (FK CASCADE)
 ├── payload: JSON
 └── created_at
```

**Konkretne instancje (katalog w §1):** `UserStateInput/Output`, `ProjectStateInput/Output`, `SessionStateInput/Output`, `WorkflowStateInput/Output`, `TaskExecutionStateInput/Output`, `GraphExecutionStateInput/Output`, `GraphNodeExecutionStateInput/Output`.

**Reguły:**
- **Append-only**: zmiana = nowy rekord. Nigdy nie modyfikujemy istniejących.
- **Reguła propagacji** (§2.2): output dziecka → input rodzica przez odpowiedni event (np. `GraphExecutionCompletedEvent` kopiuje `GraphExecutionStateOutput` do `TaskExecutionStateInput`).
- Wszystkie tabele `*Skill`, `*StateInput`, `*StateOutput` mają identyczną strukturę `{id, fk, payload, created_at}`.
- Brak tabeli polimorficznej → pełna integralność referencyjna na poziomie bazy (FK + CASCADE), prostsze indexy i query.

---

## 13. Katalog eventów (kompletny)

**Własność eventów** (enterprise rule): event jest własnością agregatu-emitenta, zapisywany w outboxie w tej samej transakcji co zmiana stanu. Inne agregaty subskrybują, ale nie są właścicielem.

**Podział na warstwy (D3):**
- **Komunikacyjne** (`*Execution*Event`): zmiana stanu agregatu, result. Przetwarzane **pierwsze**.
- **Decyzyjne** (`*Transition*Event`): decyzja routingowa Edge'a. Ewaluowane gdy inbox komunikacyjny dla noda pusty.

### 13.1 TaskExecution

| Event | Payload | Efekt |
|-------|---------|-------|
| `TaskExecutionCreatedEvent` | `task_execution_id, description, skills` | Handler tworzy pierwszy `GraphExecution` (runda #1, `parent=None`); emit `GraphExecutionCreatedEvent`. |
| `TaskExecutionStartedEvent` | `task_execution_id` | `TaskExecution → IN_PROGRESS`. |
| `TaskExecutionCompletedEvent` | `task_execution_id, output` | `TaskExecution → COMPLETED`; output → `WorkflowStateInput`. |
| `TaskExecutionFailedEvent` | `task_execution_id, reason` | `TaskExecution → FAILED`. |
| `TaskExecutionExhaustedEvent` | `task_execution_id, current_cycle, max` | `TaskExecution → EXHAUSTED`. |

### 13.2 GraphExecution

| Event | Payload | Efekt |
|-------|---------|-------|
| `GraphExecutionCreatedEvent` | `graph_execution_id, task_execution_id, parent_graph_execution_id, goal, depth` | Jeśli `parent=None`: inkrementuj `current_cycle`; jeśli `> max` → `TaskExecutionExhaustedEvent`. Goal → `GraphExecutionStateInput`. Jeśli `depth > max_subgraph_depth` → `GraphExecutionFailedEvent`. |
| `GraphPlanningStartedEvent` | `graph_execution_id` | `GraphExecution → PLANNING`. |
| `GraphSpawnedEvent` | `parent_id, child_id, goal` | Tworzy sub-graf (`parent=parent_id`). Parent zostaje w `PLANNING`. |
| `GraphPlannedEvent` | `graph_execution_id, plan` | `GraphExecution → EXECUTING`; plan → `GraphExecutionStateInput`; uruchom pierwszy node wykonawczy. |
| `SubGraphSettledEvent` | `parent_id, child_results[{id,status,result}]` | Wyniki dzieci → `GraphExecutionStateInput` parenta; parent → resume PLANNING. Emit gdy **wszystkie** dzieci parenta w stanie końcowym. |
| `GraphExecutionCompletedEvent` | `graph_execution_id, verifier_result` | `GraphExecution → COMPLETED`. Jeśli `parent=None` → `TaskExecutionCompletedEvent`. Jeśli `parent=X` → czeka na resztę dzieci X, potem `SubGraphSettledEvent`. |
| `GraphExecutionFailedEvent` | `graph_execution_id, reason` | `GraphExecution → FAILED`. Jeśli `parent=None`: replan (nowy graf `parent=None`) LUB `TaskExecutionExhaustedEvent`. Jeśli `parent=X` → wynik FAIL do parenta przez `SubGraphSettledEvent`. |

### 13.3 GraphNodeExecution (komunikacyjne)

| Event | Payload | Efekt |
|-------|---------|-------|
| `GraphNodeExecutionStartedEvent` | `node_id, role` | `Node → RUNNING`. |
| `GraphNodeExecutionCompletedEvent` | `node_id, role, result` | `Node → COMPLETED`; result → `GraphNodeExecutionStateOutput`. Jeśli `role=VERIFIER` → `GraphExecutionCompletedEvent`/`FailedEvent`. |
| `GraphNodeExecutionFailedEvent` | `node_id, role, error` | `Node → FAILED`. Jeśli `role=VERIFIER` → `GraphExecutionFailedEvent`. Jeśli `role=PLANNER` → `GraphExecutionFailedEvent`. Jeśli `AGENT/TOOLS` → Edge `ERROR_HANDLER` LUB → VERIFIER z błędem. |
| `GraphNodeExecutionTimedOutEvent` | `node_id, role` | `Node → TIMED_OUT`. Powiązany z krawędzią `TIMEOUT` (§11.2). |

### 13.4 GraphNodeTransitionExecution (decyzyjne)

| Event | Payload | Efekt |
|-------|---------|-------|
| `TransitionConditionEvaluatedEvent` | `transition_id, source_node_id, condition_result` | Ewaluacja warunku → wybór target. |
| `TransitionTakenEvent` | `transition_id, source_node_id, target_node_id` | Uruchom target node. |
| `TransitionLoopedEvent` | `transition_id, source_node_id, iteration` | Powrót do source noda. |
| `TransitionErrorHandledEvent` | `transition_id, failed_node_id, handler_node_id` | Przekierowanie do handlera błędów. |
| `TransitionTimedOutEvent` | `transition_id, node_id, handler_node_id` | Przekierowanie po timeout. |

> Współbieżność nie ma osobnego eventu — fan-out jest wyrażony przez wiele `GraphSpawnedEvent`-ów emitowanych w ramach jednego `SPAWN_SUBGRAPH`-step PLANNERA, a zbieranie przez `SubGraphSettledEvent` (§13.2).

---

## 14. Scheduler — głupi orkiestrator

Scheduler **nie zna biznesu**. Działa w pętli, tylko przenosi eventy i, gdy nic się nie dzieje, podnosi grafy `PENDING`.

```
1. Opróżnij INBOX (warstwa komunikacyjna pierwsza — D3)
   └── dla każdego eventu komunikacyjnego → dispatch do handlera
       (handlery zmieniają stany agregatów, emitują nowe eventy → OUTBOX)

2. Przepisz OUTBOX → INBOX

3. Gdy INBOX komunikacyjny pusty → ewaluuj Edge'e (warstwa decyzyjna)
   └── dla nodów w stanie końcowym bez podjętej decyzji → ewaluuj outgoing transitions
       → emit Transition*Event → OUTBOX → wróć do kroku 2

4. Gdy INBOX i OUTBOX puste → znajdź graf do startu
   ├── kryteria (wszystkie muszą być spełnione):
   │   a) GraphExecution.status == PENDING
   │   b) parent_graph_execution_id IS NULL  LUB  parent w stanie PLANNING
   │   c) TaskExecution.status == IN_PROGRESS
   │   d) current_cycle <= max_planning_cycles
   └── uruchom PLANNERA → emit GraphPlanningStartedEvent
```

**Scheduler NIE wznawia parenta po sub-grafach** — robi to wyłącznie `SubGraphSettledEvent`.
**Scheduler NIE decyduje o replanie** — robi to handler `GraphExecutionFailedEvent`.

---

## 15. Sub-grafy — mechanizm i obsługa

### 15.1 Cykl życia sub-grafu

```
Parent PLANNER (status: PLANNING)
   │
   ├── emit GraphSpawnedEvent (goal="...")
   │     └── tworzy GraphExecution C: parent_graph_execution_id=Parent, depth=Parent.depth+1
   │           └── C.current_cycle NIE inkrementowane
   │
   ▼
Parent pozostaje w PLANNING (scheduler nie rusza — niezakonczone dzieci)
   │
   │  (C przechodzi swój pipeline PLANNER→...→VERIFIER)
   │
   ├── C.COMPLETED → wynik w C.GraphExecutionStateOutput
   └── C.FAILED    → reason w C.GraphExecutionStateOutput
   │
   ▼
Gdy wszystkie dzieci Parenta w stanie końcowym → SubGraphSettledEvent
   │
   ▼
Parent → resume PLANNING
   └── Parent.GraphExecutionStateInput wzbogacony o children_results
   └── PLANNER rodzica decyduje z uwzględnieniem wyników
```

### 15.2 Równoległość sub-grafów

- PLANNER może w jednym kroku spawnąć **wiele sub-grafów** (wiele GraphExecution z tym samym `parent_graph_execution_id`).
- Sub-grafy **równoległe i niezależne** — scheduler uruchamia je współbieżnie.
- Parent ma niezakonczone dzieci aż **wszystkie** osiągną stan końcowy.
- `SubGraphSettledEvent` emitowany dopiero po ostatnim dziecku.

### 15.3 Obsługa FAILED sub-grafu

Gdy sub-graf `C` → `FAILED`, rodzic dostaje `children_results` ze statusem FAIL + reason. PLANNER rodzica ma trzy opcje:

| Decyzja | Warunek | Akcja |
|---------|---------|-------|
| **Akceptuj porażkę, dostosuj plan** | Wynik nieblokujący | Kontynuuj planowanie z notką o porażce → EXECUTING. |
| **Re-spawn sub-grafu z poprawionym celem** | Blisko sukcesu, inna strategia | Spawn nowego sub-grafu z tym samym parentem. |
| **Fail rodzica** | Blokujące, brak strategii | Emit `GraphExecutionFailedEvent`. Jeśli `parent=None` → replan/EXHAUSTED. Jeśli `parent=X` → fail bubluje przez `SubGraphSettledEvent`. |

**Sub-grafy NIE replanują wewnętrznie.** Tylko grafy główne (`parent=None`) replanują i inkrementują `current_cycle`.

### 15.4 Rekurencja (D5)

- Sub-graf może spawnować własne sub-grafy — ten sam mechanizm.
- Limit `max_subgraph_depth` (zalecane 5). Przekroczenie → `GraphExecutionFailedEvent`.

---

## 16. Replan rundy głównej

```
Verifier głównego GraphExecution X → FAIL
   │
   ▼
emit GraphExecutionFailedEvent(graph_execution_id=X, reason)
   │
   ▼
GraphExecution X → FAILED (nierewersybilne)
   │
   ▼
Handler sprawdza:
   ├── next_cycle = TaskExecution.current_cycle + 1
   ├── if next_cycle > max_planning_cycles:
   │       └── emit TaskExecutionExhaustedEvent → EXHAUSTED
   └── else:
           └── emit GraphExecutionCreatedEvent(
                   task_execution_id,
                   parent_graph_execution_id=None,
                   goal="replan: " + X.description,
                   state_input.previous_attempt_id = X.id
               )
               └── inkrementuje current_cycle (= next_cycle)
               └── GraphExecutionStateOutput X kopiowane do GraphExecutionStateInput nowego grafa
```

- Replan **zawsze nowy** `GraphExecution` z `parent=None` — audit trail zachowany.
- **Brak flagi "replanowalności"** — każdy FAILED rundy głównej idzie do replanu; ogranicznik = `max_planning_cycles`.

---

## 17. Scenariusz end-to-end

```
User/System → Import/API
   │
   ▼
emit TaskExecutionCreatedEvent (current_cycle=0, max_planning_cycles=5)
   │
   ▼
Handler → tworzy GraphExecution G1 (parent=None)
   └── emit GraphExecutionCreatedEvent → current_cycle=1, TaskExecution → IN_PROGRESS
   │
   ▼
Scheduler (inbox pusty) → znajduje G1 PENDING → uruchom PLANNERA
   │
   ▼
PLANNER G1 (emit GraphPlanningStartedEvent → G1.PLANNING)
   ├── Scenariusz A (plan bezpośredni):
   │   └── emit GraphPlannedEvent → G1.EXECUTING
   │       └── AGENT/TOOLS → NodeCompleted → Edge SEQUENCE → VERIFIER
   │           ├── OK  → GraphExecutionCompletedEvent → G1.COMPLETED
   │           │        └── parent=None → TaskExecutionCompletedEvent → COMPLETED
   │           └── FAIL → GraphExecutionFailedEvent → G1.FAILED
   │                    └── next_cycle=2 ≤5 → GraphExecutionCreatedEvent(parent=None) → runda #2
   │
   └── Scenariusz B (spawn sub-grafu):
       └── emit GraphSpawnedEvent(goal="analiza X")
           └── tworzy G2 (parent=G1, depth=1)
           └── G1 zostaje w PLANNING (niezakonczone dzieci)
               └── scheduler uruchamia G2 (PLANNER→...→VERIFIER)
                   ├── G2.COMPLETED → wynik w G2.GraphExecutionStateOutput
                   └── po ostatnim dziecku → SubGraphSettledEvent(parent=G1)
                       └── children_results → G1.GraphExecutionStateInput → resume PLANNERA G1
```

---

## 18. Ortogonalne (nie wpływają na rdzeń)

Istnieją w kodzie, ale nie ruszają maszyn stanów:

- **RAG** (`RagDocument`, `RagChunk`, embeddingi, `SearchSimilarQuery`) — wyszukiwanie semantyczne; źródło wiedzy dla AGENT/PLANNER.
- **RunnerConfig** (`kind: "python"`, `body`) — konfiguracja runnerów; używana przez TOOLS do deterministycznego wykonania.

Mogą być dodawane warstwowo bez wpływu na agregaty rdzenia.

---

## 19. Minimalny zestaw do startu maszynerii

Aby system ruszył, **muszą istnieć**:

1. **Agregaty**: User, Project, Session, AgentConfigExecution, Workflow, TaskExecution, GraphExecution, GraphNodeExecution, GraphNodeTransitionExecution, AgentExecution.
2. **Encje skili** (osobne tabele per agregat, z FK): `UserSkill`, `ProjectSkill`, `SessionSkill`, `WorkflowSkill`, `TaskExecutionSkill`, `GraphExecutionSkill`, `AgentSkillExecution`.
3. **Encje state** (osobne tabele per agregat, z FK, append-only): `*StateInput`, `*StateOutput` dla User, Project, Session, Workflow, TaskExecution, GraphExecution, GraphNodeExecution (katalog w §1).
4. **Value object platformy**: `Message` (komendy/eventy/zapytania).
5. **Maszyny stanów**: TaskExecution (§8.2), GraphExecution (§9.2), GraphNodeExecution.
6. **Katalog eventów**: §13 (komunikacyjne + decyzyjne).
7. **Scheduler**: pętla inbox→outbox + podnoszenie PENDING (§14).
8. **Reguły**: `parent_graph_execution_id` (§2.1), propagacja Stage (§2.2), `current_cycle` (§8.3), replan (§16), sub-grafy (§15).
9. **Value objects only**: agregaty używają wyłącznie value objectów (VO) — żadnych prymitywów (`str`, `int`, `bool`, `dict`) w sygnaturach metod, polach stanu ani eventach. Każda dana domenowa musi być opakowana w VO (np. `TaskId`, `NodeRole`, `SkillPayload`, `ExecutionStatus`). Zapewnia to samowalidację, type safety i eliminuje primitive obsession.
10. **Subdomena `user`**: agregat `User` znajduje się w wydzielonej subdomenie o nazwie `user`. Jest to osobny bounded context z własnym modelem, repozytorium i portami. Reszta systemu komunikuje się z nim wyłącznie przez porty (ACL).
11. **Subdomena `projekt`**: agregat `Project` znajduje się w wydzielonej subdomenie o nazwie `projekt`. Jest to osobny bounded context z własnym modelem, repozytorium i portami. Reszta systemu komunikuje się z nim wyłącznie przez porty (ACL).

Reszta (RAG, RunnerConfig, UI, persystencja, infrastruktura Envelope) to warstwy ortogonalne i mogą być dodawane niezależnie.
