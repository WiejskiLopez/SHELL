# Domain Architecture v2 — SHELL

> Wersja bazowa: `DOMAIN.md`. V2 naprawia luki logiczne bazowej bez zmiany koncepcji:
> - ustala poprawne użycie `parent_graph_execution_id` (replan = `None`, sub-graf = `<id>`),
> - definiuje `SubGraphSettledEvent` jako mechanizm wznowienia rodzica po sub-grafach (bez sztucznego stanu — "parent czeka" jest wyprowadzalne z query po `parent_graph_execution_id`),
> - definiuje pełen katalog eventów i jednoznaczną maszynę stanów,
> - precyzuje reguły inkrementacji `current_cycle`,
> - określa zachowanie rodzica przy `FAILED` sub-grafu,
> - określa domyślną kolejność nodów (PLANNER → AGENT → TOOLS → VERIFIER), z niestandardowymi przejściami przez `GraphNodeTransitionExecution` jako mechanizm decyzyjny krawędzi grafu (§16),
> - usuwa sztuczną flagę `replanable` — każdy FAILED idzie do replanu, jedynym ograniczeniem jest `max_planning_cycles`.

---

## 1. Przegląd agregatów

| Agregat | Odpowiedzialność | Kluczowe ID |
|---------|-----------------|-------------|
| **Session** | Zna skille użytkownika i projektu w momencie otwarcia sesji; zamrożony snapshot. | `session_id` |
| **AgentConfigExecution** | Konfiguracja agentów (model, temp, max_tokens) wybrana przez użytkownika w sesji. | `agent_config_execution_id` → `session_id` |
| **Workflow** | Zna architekturę, zasady, wymagania projektu/subprojektu. | `workflow_id` → `session_id` |
| **TaskExecution** | Życiorys jednego zadania — cel, limit rund, aktualna runda. | `task_execution_id` → `workflow_id` |
| **GraphExecution** | Jedna runda planowania → wykonania → weryfikacji. `parent_graph_execution_id=None` → graf główny rundy; `<id>` → sub-graf. | `graph_execution_id` → `task_execution_id` |
| **GraphNodeExecution** | Pojedynczy krok w rundzie (PLANNER / AGENT / TOOLS / VERIFIER). Jeśli `role=AGENT` → `agent_execution_id`. | `graph_node_execution_id` → `graph_execution_id` |
| **AgentExecution** | Znacznik "to GraphNodeExecution było agentem"; agreguje skille użyte przy wykonaniu. | `agent_execution_id` → `graph_node_execution_id` |
| **AgentSkillExecution** | Pojedynczy skill użyty przez agenta w jednym wykonaniu (append-only archive). | `agent_skill_execution_id` → `agent_execution_id` |

## 2. Hierarchia agregatów

```
Session
 └── AgentConfigExecution (session_id)        # konfig LLM dla całej sesji
 └── Workflow (session_id)
      └── TaskExecution (workflow_id, max_planning_cycles, current_cycle)
           │
           ├── GraphExecution A ── runda #1, parent_graph_execution_id=None
           │    │
           │    │  (Pipeline liniowy w ramach grafa)
           │    ├── GraphNodeExecution: PLANNER
           │    │     ├── emit GraphPlannedEvent (gdy koniec planowania)
           │    │     └── LUB emit GraphSpawnedEvent (gdy spawn sub-grafu)
           │    ├── GraphNodeExecution: AGENT (opcjonalny)
           │    │     └── AgentExecution
           │    │          ├── AgentSkillExecution
           │    │          └── AgentSkillExecution
           │    ├── GraphNodeExecution: TOOLS (opcjonalny)
           │    └── GraphNodeExecution: VERIFIER
           │
           │  (Sub-grafy spawnnięte przez PLANNERA grafa A — równoległe, niezależne)
           ├── GraphExecution C ── parent_graph_execution_id=A
           ├── GraphExecution D ── parent_graph_execution_id=A
           │
           │  (Replan: A zakończony FAILED → nowy graf główny rundy #2)
            └── GraphExecution B ── parent_graph_execution_id=None  (runda #2)
                 └── state_input.previous_attempt_id = A  (link audytowy w stanie wejściowym)
```

**Zasady `parent_graph_execution_id`:**

| Wartość | Znaczenie | Inkrementuje `current_cycle`? |
|---------|-----------|------------------------------|
| `None` | Graf główny rundy (pierwsza runda LUB replan). | **TAK** |
| `<GraphExecutionId>` | Sub-graf spawnnięty przez PLANNERA grafu wskazanego. Parent czeka na wynik. | **NIE** |

- **Jedno pole, jedna relacja.** Dyskryminatorem jest wartość `None` vs `<id>`.
- **Replan = nowy graf główny** (`parent=None`). Dane poprzedniej próby są dostępne przez `state_input` (patrz §8.1).
- **Sub-graf = `parent=<id>`**. Parent pozostaje w stanie `PLANNING` (PLANNER jeszcze nie wyemitował `GraphPlannedEvent`); scheduler traktuje go jako "zajęty, ma niezakonczone dzieci" i nie rusza jego nodów.
- Relacja sub-grafu jest **jednokierunkowa**: child zna `parent_graph_execution_id`. Parent NIE przechowuje listy dzieci — dzieci znajduje się query'm (`WHERE parent_graph_execution_id = ?`).
- Sub-graf NIE replanuje wewnętrznie — jeśli się nie uda, parent PLANNER decyduje co dalej (patrz §11.3).

## 3. Session — zamrożony snapshot skilli

```
Session
 ├── id
 ├── user_id
 ├── project_id
 ├── status: OPEN | CLOSED
 ├── opened_at
 └── closed_at (nullable)
```

- Sesja jest otwierana na początku interakcji z projektem. Nie przechowuje wiadomości — to nie jest chat.
- Skille użytkownika i projektu są **zamrażane** w momencie otwarcia sesji (append-only do momentu zamknięcia sesji; modyfikacje poza sesją nie wpływają na bieżące wykonania).
- Workflow dziedziczy skille z sesji i może je rozszerzać o skille architektury/wymagań.

### 3.1 Tabele skilli sesji

| Tabela | Zawartość |
|--------|-----------|
| `session_user_skill` | Skille użytkownika — z configu, preferencji, historii |
| `session_project_skill` | Skille projektu — konwencje, toolchain, CI/CD |

```
[SessionSkill]
 ├── id: str (PK)
 ├── session_id: str (FK → session.id CASCADE)
 ├── payload: JSON
 └── created_at: datetime
```

## 4. AgentConfigExecution — konfiguracja LLM w sesji

```
AgentConfigExecution
 ├── id: str (PK)
 ├── session_id: str (FK → session.id CASCADE, UNIQUE)   # max 1 rekord na sesję
 ├── config: dict          # model, temperature, max_tokens, top_p, ...
 ├── created_at: datetime
 └── updated_at: datetime
```

- **`session_id` ma CONSTRAINT UNIQUE** — wymuszone na poziomie bazy, że na jedną sesję przypada co najwyżej jeden `AgentConfigExecution`. Próba INSERT drugiego rekordu dla tego samego `session_id` → błąd bazy (np. `UNIQUE constraint failed`).
- `AgentConfigExecution` jest źródłem configu LLM dla **wszystkich nodów typu LLM** — zarówno `PLANNER` jak i `AGENT`. Gdy `GraphNodeExecution(role=AGENT)` tworzy `AgentExecution`, config jest pobierany z jedynego `AgentConfigExecution` dla `session_id`.
- Pierwszy INSERT dla sesji tworzy rekord; kolejne zmiany konfiguracji w ramach sesji to **UPDATE** istniejącego rekordu, nie INSERT (append-only nie ma tu sensu — chcemy jednego aktualnego configu).
- Jeśli sesja nie ma jeszcze rekordu → agent używa configu domyślnego (zdefiniowanego w kodzie) LUB tworzenie agenta failuje (decyzja implementacyjna; zalecane: domyślny config).

## 5. Workflow — architektura i reguły

```
Workflow
 ├── id
 └── session_id
```

Wszystkie reguły/zasady/wymagania są **skillami** (JSON w osobnych tabelach), a nie polami bezpośrednio na Workflow.

### 5.1 Tabele skilli workflow

| Tabela | Zawartość |
|--------|-----------|
| `project_skill` | Skille projektu — konwencje, technologie, struktura repo |
| `architecture_skill` | Skille architektury — wzorce, warstwy, zależności |
| `requirement_skill` | Skille wymagań — funkcjonalne, niefunkcjonalne, biznesowe |

```
[WorkflowSkill]
 ├── id: str (PK)
 ├── workflow_id: str (FK → workflow.id CASCADE)
 ├── payload: JSON
 └── created_at: datetime
```

- Każda tabela jest append-only, 0..N wierszy na workflow.
- Workflow nie zarządza nodami — to rola TaskExecution/GraphExecution.

## 6. Przepływ skilli (Session → Workflow → TaskExecution → Agent)

```
Session
 ├── session_user_skill.payload
 └── session_project_skill.payload
     │
     ▼
Workflow
 ├── project_skill.payload
 ├── architecture_skill.payload
 └── requirement_skill.payload
     │
     ▼ (kopia w momencie tworzenia TaskExecution)
TaskExecutionSkill
 └── task_execution_id, payload  # zamrożona kopia skilli z Session+Workflow
     │
     ▼ (PLANNER/AGENT czytają bezpośrednio z TaskExecutionSkill po task_execution_id)
GraphNodeExecution(role=AGENT)
 └── AgentExecution
      └── AgentSkillExecution (append-only archive — co agent faktycznie dostał)
```

**Reguły:**
- W momencie utworzenia `TaskExecution` wszystkie skille z `Session` + `Workflow` są kopiowane do tabeli `TaskExecutionSkill` (jeden wiersz na skill). Zmiany w sesji/workflow po utworzeniu `TaskExecution` nie wpływają na to zadanie.
- `AgentSkillExecution` jest archiwum — zapisywane w momencie uruchomienia agenta, dokładnie to, co agent otrzymał (subset z `TaskExecutionSkill` wybrany przez Planera).

### 6.1 TaskExecutionSkill — zamrożone skille zadania

```
TaskExecutionSkill
 ├── id: str (PK)
 ├── task_execution_id: str (FK → task_execution.id CASCADE)
 ├── skill_source: str          # "session.user" | "session.project" | "workflow.project" | "workflow.architecture" | "workflow.requirement"
 ├── payload: JSON
 └── created_at: datetime
```

- Append-only: wiersze są dodawane w momencie utworzenia `TaskExecution` i nigdy nie są modyfikowane.
- `skill_source` określa pochodzenie (dla audytowalności).
- PLANNER/AGENT czytają skille zadania przez query po `task_execution_id`.

## 7. TaskExecution — cykl życia

### 7.1 Pola

```
TaskExecution
 ├── id
 ├── workflow_id
 ├── name: str                        # nazwa zadania (z importu/API)
 ├── description: str                 # cel zadania (z pierwszego StateInput)
 ├── max_planning_cycles: int         # limit rund głównych (np. 5)
 ├── current_cycle: int               # liczba rozpoczętych rund głównych
 ├── status: CREATED | IN_PROGRESS | COMPLETED | FAILED | EXHAUSTED
 ├── work_dir: str                    # katalog roboczy zadania
 └── state_inputs: List[TaskExecutionStateInput]  # append-only log payloadów
```

### 7.2 Maszyna stanów

```
[CREATED] ──TaskExecutionStartedEvent──▶ [IN_PROGRESS]
                                              │
                              ┌───────────────┼───────────────┐
                              │               │               │
            TaskExecutionCompletedEvent  TaskExecutionFailedEvent  TaskExecutionExhaustedEvent
                              │               │               │
                         [COMPLETED]      [FAILED]       [EXHAUSTED]
```

- `CREATED → IN_PROGRESS`: emitowane gdy tworzony jest pierwszy `GraphExecution` rundy głównej (trigger: `GraphExecutionCreatedEvent` z `parent_graph_execution_id=None`).
- `IN_PROGRESS → COMPLETED`: gdy główny `GraphExecution` (rundy bieżącej) zakończy się `COMPLETED`.
- `IN_PROGRESS → FAILED`: nieodwracalny błąd zadania (np. verifier zgłosił błąd niereplanowalny — patrz §11.3).
- `IN_PROGRESS → EXHAUSTED`: `current_cycle >= max_planning_cycles` przy próbie kolejnego replanu (patrz §12).

### 7.3 Reguły `current_cycle`

- `current_cycle` zaczyna od **0** przy `CREATED`.
- **Każdy graf z `parent_graph_execution_id=None`** inkrementuje `current_cycle` w momencie utworzenia:
  - Pierwszy graf rundy #1 → `current_cycle = 1`.
  - Replan (runda #2) → `current_cycle = 2`.
  - itd.
- **Sub-grafy (`parent_graph_execution_id=<id>`) NIE inkrementują** `current_cycle` (to nie jest nowa runda, tylko rozszerzenie bieżącej).
- `max_planning_cycles` to maksymalna liczba rund głównych. Jeśli próba utworzenia grafu rundy `current_cycle + 1` przekracza limit → `TaskExecution.EXHAUSTED` (zamiast tworzenia grafu).
- Dopuszczalne rundy główne: `1..max_planning_cycles`.

## 8. GraphExecution — cykl życia (jedna runda)

### 8.1 Pola

```
GraphExecution
 ├── id
 ├── task_execution_id
 ├── parent_graph_execution_id: GraphExecutionId | None  # None=graf główny rundy; <id>=sub-graf
```

- **Stan wejściowy (`GraphExecutionStateInput`)** — dane wejściowe dla grafa: cel zadania (`goal`), `previous_attempt_id` (dla replanu), wyniki sub-grafów po `SubGraphSettledEvent`. Append-only log (każda zmiana to nowy rekord z `is_current`).
- **Stan wyjściowy (`GraphExecutionStateOutput`)** — dane wyjściowe grafa: wynik VERIFIER, wyniki pośrednie nodów. Append-only log.
- Parent NIE przechowuje listy dzieci. Dzieci parenta znajduje się query'm po `parent_graph_execution_id`.
- Graf NIE przechowuje listy nodów. Nody grafa znajduje się query'm po `graph_execution_id`.

### 8.2 Maszyna stanów

```
[PENDING] ─GraphPlanningStartedEvent─▶ [PLANNING]
                                            │
                              ┌─────────────┴─────────────┐
                              │                           │
                  GraphSpawnedEvent              GraphPlannedEvent
                  (spawn sub-grafu)              (koniec planowania)
                              │                           │
                              ▼                           ▼
              [PLANNING] (utrzymane —             [EXECUTING]
               parent ma niezakonczone
               dzieci; scheduler
               nie rusza nodów parenta)
                              │
                  SubGraphSettledEvent
                  (wszystkie dzieci OK/Fail)
                              │
                               ▼
               PLANNER wznowiony z wynikami
               sub-grafów w state_input; emit GraphPlannedEvent
                  LUB GraphSpawnedEvent (kolejny spawn)
                              │
                              ▼
                         [EXECUTING]
                                            │
                                GraphNodeExecutionCompletedEvent
                                /FailedEvent (AGENT/TOOLS)
                                            │
                                            ▼
                                       [VERIFYING]
                                            │
                                  ┌─────────┴─────────┐
                                  │                   │
                       GraphExecutionCompletedEvent  GraphExecutionFailedEvent
                                  │                   │
                             [COMPLETED]           [FAILED]
```

**Nierewersybilne stany końcowe:** `COMPLETED`, `FAILED`. Brak powrotu z końcowych — replan to **nowy** `GraphExecution` z `parent=None`, nie reset stanu.

**"Parent czeka na sub-grafy" nie jest osobnym stanem.** Parent pozostaje w `PLANNING` (bo PLANNER nie wyemitował jeszcze `GraphPlannedEvent`). Scheduler wykrywa "zajętość" parenta query'm: czy istnieją GraphExecution z `parent_graph_execution_id = parent.id` w stanie ≠ `COMPLETED`, ≠ `FAILED`. Jeśli tak — parent ma niezakonczone dzieci, scheduler nie rusza jego nodów. `SubGraphSettledEvent` jest sygnałem do wznowienia PLANNERA rodzica z wynikami dzieci zapisanymi w `GraphExecutionStateInput` parenta.

### 8.3 Kiedy PLANNER spawnuje sub-graf

| Scenariusz | Opis |
|------------|------|
| **Human in the loop** | PLANNER potrzebuje zadać pytanie użytkownikowi. Spawnuje sub-graf ze skillem `ask_user`. Wynik wraca do PLANNERA rodzica. |
| **Podział zadania** | PLANNER dzieli zadanie na pod-zadania. Każdy pod-zadanie = osobny sub-graf z `payload.goal`. Sub-grafy działają **równolegle i niezależnie**. |
| **Dodatkowa analiza** | PLANNER potrzebuje więcej informacji (np. "przeszukaj dokumentację", "przeanalizuj moduł X"). |

## 9. GraphNodeExecution — krok w rundzie

### 9.1 Pola

```
GraphNodeExecution
 ├── id
 ├── graph_execution_id
 ├── role: PLANNER | AGENT | TOOLS | VERIFIER
 ├── order: int                  # kolejność w pipeline (0,1,2,3)
```

### 9.2 Pipeline (domyślny — liniowy)

Domyślna kolejność nodów w ramach jednego `GraphExecution`:

```
PLANNER (order=0) → AGENT (order=1, opcjonalny) → TOOLS (order=2, opcjonalny) → VERIFIER (order=3)
```

- Kolejność domyślna jest **liniowa**, zdefiniowana przez `order`.
- **PLANNER i VERIFIER są obowiązkowe**; AGENT i TOOLS opcjonalne (PLANNER może zdecydować o pominięciu).
- AGENT wykonuje pracę opartą na LLM ze skillemi; TOOLS wykonuje deterministyczne wywołania tooli (nie wymaga LLM). Mogą wystąpić oba kolejno.
- Jeśli `role=AGENT` → `agent_execution_id` wskazuje na `AgentExecution`. W przeciwnym razie `agent_execution_id=None`.
- VERIFIER może zakończyć graf `COMPLETED` (OK) lub `FAILED` (FAIL → replan w TaskExecution, patrz §12).

**Niestandardowe przejścia:** dla przypadków wymagających rozgałęzień, pętli, warunków lub równoległości, routing między nodami jest definiowany przez `GraphNodeTransitionExecution` (patrz §16). Domyślny pipeline liniowy jest szczególnym przypadkiem — automatycznie tworzy `SEQUENCE` krawędzie między kolejnymi nodami.

### 9.3 AgentExecution i AgentSkillExecution

```
AgentExecution
 ├── id
 └── graph_node_execution_id
```
- Znacznik "to GraphNodeExecution było agentem"; agreguje skille użyte przy wykonaniu.
- Config LLM pobierany z `AgentConfigExecution` (via `session_id` → `workflow_id` → `task_execution_id` → `graph_execution_id` → `graph_node_execution_id`).
- Rezultat agenta ląduje w `GraphNodeExecution.result`.

```
AgentSkillExecution
 ├── id
 ├── agent_execution_id
  ├── skill_source: str          # "session.user" | "session.project" | "workflow.architecture" | "workflow.requirement" | "task.base"
 ├── payload: JSON
 └── created_at: datetime
```
- Append-only archiwum tego, co agent faktycznie otrzymał w jednym wykonaniu.
- `skill_source` określa pochodzenie (dla audytowalności).

## 10. Katalog eventów (kompletny)

**Własność eventów:** Każdy event jest własnością agregatu, który go emituje:
- `TaskExecution*Event` → `TaskExecution`
- `GraphExecution*Event` → `GraphExecution`
- `GraphNodeExecution*Event` → `GraphNodeExecution`

To oznacza, że event jest zapisywany w outboxie w tej samej transakcji co zmiana stanu agregatu. Inne agregaty mogą nasłuchiwać (subskrybować) eventy innych agregatów, ale nie są ich właścicielami.

### 10.1 TaskExecution

| Event | Payload | Efekt |
|-------|---------|-------|
| `TaskExecutionCreatedEvent` | `task_execution_id`, `description`, `skills` | Handler tworzy pierwszy `GraphExecution` (runda #1, `parent_graph_execution_id=None`); emituje `GraphExecutionCreatedEvent`; `TaskExecution → IN_PROGRESS`. |
| `TaskExecutionCompletedEvent` | `task_execution_id` | `TaskExecution → COMPLETED`. |
| `TaskExecutionFailedEvent` | `task_execution_id`, `reason` | `TaskExecution → FAILED`. |
| `TaskExecutionExhaustedEvent` | `task_execution_id`, `current_cycle`, `max_planning_cycles` | `TaskExecution → EXHAUSTED`. |

### 10.2 GraphExecution

| Event | Payload | Efekt |
|-------|---------|-------|
| `GraphExecutionCreatedEvent` | `graph_execution_id`, `task_execution_id`, `parent_graph_execution_id`, `goal` | Inkrementuje `current_cycle` jeśli `parent_graph_execution_id=None` (runda główna). Jeśli `current_cycle > max_planning_cycles` → emit `TaskExecutionExhaustedEvent` zamiast tworzenia. Goal trafia do `GraphExecutionStateInput`. |
| `GraphPlanningStartedEvent` | `graph_execution_id` | `GraphExecution → PLANNING`. |
| `GraphSpawnedEvent` | `graph_execution_id` (parent), `child_graph_execution_id`, `goal` | Tworzy nowy sub-graf (`parent_graph_execution_id=parent`). Goal trafia do `GraphExecutionStateInput` dziecka. Parent pozostaje w `PLANNING` — scheduler sam wykryje (query'm po `parent_graph_execution_id`), że ma niezakonczone dzieci i nie ruszy jego nodów. |
| `GraphPlannedEvent` | `graph_execution_id`, `plan` | `GraphExecution → EXECUTING`; plan zapisywany w `GraphExecutionStateInput`; uruchom pierwszy node wykonawczy (AGENT lub TOOLS). |
| `SubGraphSettledEvent` | `parent_graph_execution_id`, `child_results: List[{graph_execution_id, status, result}]` | Wyniki sub-grafów zapisywane w `GraphExecutionStateInput` parenta; `parent → PLANNING` (resume PLANNERA). Emitowany gdy **wszystkie** sub-grafy parenta są w stanie końcowym (`COMPLETED` lub `FAILED`). |
| `GraphExecutionCompletedEvent` | `graph_execution_id`, `verifier_result` | `GraphExecution → COMPLETED`. Wynik VERIFIER w `GraphExecutionStateOutput`. Jeśli `parent_graph_execution_id=None` (runda główna) → emit `TaskExecutionCompletedEvent`. Jeśli `parent_graph_execution_id=X` → czeka aż wszystkie sub-grafy X się skończą, wtedy `SubGraphSettledEvent`. |
| `GraphExecutionFailedEvent` | `graph_execution_id`, `reason` | `GraphExecution → FAILED`. Jeśli `parent_graph_execution_id=None` (runda główna) → emit `GraphExecutionCreatedEvent` z `parent_graph_execution_id=None` (replan), chyba że `current_cycle >= max_planning_cycles` → wtedy `TaskExecutionExhaustedEvent`. Przyczynę faila zapisuje się w `GraphExecutionStateOutput` i kopiuje do `GraphExecutionStateInput` nowej rundy. Jeśli `parent_graph_execution_id=X` → czeka na pozostałe sub-grafy X, potem `SubGraphSettledEvent` (parent dostaje status FAILED tego dziecka). |

### 10.3 GraphNodeExecution

| Event | Payload | Efekt |
|-------|---------|-------|
| `GraphNodeExecutionStartedEvent` | `graph_node_execution_id`, `role` | `GraphNodeExecution → RUNNING`. |
| `GraphNodeExecutionCompletedEvent` | `graph_node_execution_id`, `role`, `result` | `GraphNodeExecution → COMPLETED`. Jeśli `role=VERIFIER` → emit `GraphExecutionCompletedEvent`. W przeciwnym razie → uruchom następny node w pipeline (wg `order`). |
| `GraphNodeExecutionFailedEvent` | `graph_node_execution_id`, `role`, `error` | `GraphNodeExecution → FAILED`. Jeśli `role=VERIFIER` → emit `GraphExecutionFailedEvent`. Jeśli `role=PLANNER` → `GraphExecutionFailedEvent` (replan spróbuje wywołać planera ponownie; limitem jest `max_planning_cycles`). Jeśli `role=AGENT` lub `TOOLS` → przejście do VERIFIER z błędem w `state_output` (verifier oceni wynik). |

## 11. Sub-grafy — mechanizm i obsługiwane przypadki

### 11.1 Cykl życia sub-grafu

```
Parent PLANNER (status: PLANNING)
   │
   ├── emit GraphSpawnedEvent (goal="...")
   │     └── tworzy GraphExecution C: parent_graph_execution_id=Parent
   │           └── C.current_cycle NIE inkrementowane (to sub-graf)
   │
   ▼
Parent pozostaje w PLANNING (scheduler nie rusza — ma niezakonczone dzieci)
   │
   │  (C przechodzi przez swój pipeline: PLANNER→...→VERIFIER)
   │
   ├── C.COMPLETED  → wynik w C.state_output
   └── C.FAILED     → reason w C.state_output
   │
   ▼
Gdy wszystkie dzieci Parenta w stanie końcowym → SubGraphSettledEvent
   │
   ▼
Parent → PLANNING (resume)
   └── Parent.state_input wzbogacony o children_results = wyniki wszystkich dzieci
   └── PLANNER rodzica podejmuje decyzję z uwzględnieniem wyników
```

### 11.2 Równoległość sub-grafów

- PLANNER może w jednym kroku planowania spawnąć **wiele sub-grafów** (wiele rekordów GraphExecution z tym samym `parent_graph_execution_id`).
- Sub-grafy są **równoległe i niezależne** — scheduler może je uruchamiać współbieżnie.
- Parent ma niezakonczone dzieci aż **wszystkie** dzieci osiągną stan końcowy (`COMPLETED`/`FAILED`). Scheduler w tym czasie nie uruchamia nodów parenta (wykrywa query'm po `parent_graph_execution_id`).
- `SubGraphSettledEvent` jest emitowany dopiero gdy ostatnie dziecko się zakończy.

### 11.3 Obsługa FAILED sub-grafu

Gdy sub-graf `C` zakończy się `FAILED`, rodzic dostaje w `children_results` status `FAILED` + `reason`. PLANNER rodzica ma trzy opcje:

| Decyzja PLANNERA rodzica | Warunek | Akcja |
|--------------------------|---------|-------|
| **Akceptuj porażkę i dostosuj plan** | Wynik sub-grafu nieblokujący | Kontynuuj planowanie z notką o porażce; przejdź do EXECUTING. |
| **Re-spawn sub-grafu z poprawionym celem** | Sub-graf blisko sukcesu, potrzebuje innej strategii | Spawn nowego sub-grafu z `parent_graph_execution_id=Parent` (kolejny rekord z tym samym parentem); Parent nadal w `PLANNING` z niezakonczonymi dziećmi. |
| **Fail rodzica** | Wynik sub-grafu blokujący, brak strategii | Parent.VERIFIER (lub PLANNER) emituje `GraphExecutionFailedEvent`. Jeśli `parent_graph_execution_id=None` → replan rundy (lub `EXHAUSTED` gdy limit). Jeśli `parent_graph_execution_id=<X>` → fail sub-grafu, parent X dostaje wynik przez `SubGraphSettledEvent`. |

**Sub-grafy NIE replanują wewnętrznie.** Jeśli sub-graf `C` zakończy się `FAILED`, nie jest tworzony automatycznie nowy graf jako replan C. Zamiast tego parent PLANNER dostaje wynik i sam decyduje czy:
- dostosować plan,
- spawnąć nowy sub-graf (re-spawn z poprawionym celem),
- zfailować siebie.

To upraszcza model — tylko grafy główne (`parent=None`) replanują, i tylko one inkrementują `current_cycle`.

### 11.4 Rekurencja

- Sub-graf może spawnować własne sub-grafy (rekurencja) — ten sam mechanizm.
- Limit głębokości: zalecane `max_subgraph_depth` (np. 5) — ochrona przed nieskończoną rekurencją. Przekroczenie → `GraphExecutionFailedEvent`.

## 12. Replan rundy głównej — mechanizm

```
Verifier głównego GraphExecution → FAIL
   │
   ▼
emit GraphExecutionFailedEvent(graph_execution_id=X, reason=...)
   │
   ▼
GraphExecution X → FAILED (nierewersybilne)
   │
   ▼
Handler sprawdza:
   ├── next_cycle = TaskExecution.current_cycle + 1
   ├── if next_cycle > max_planning_cycles:
   │       └── emit TaskExecutionExhaustedEvent → TaskExecution.EXHAUSTED
   └── else:
           └── emit GraphExecutionCreatedEvent(
                   task_execution_id,
                   parent_graph_execution_id=None,
                   goal="replan: " + X.description,
               )
               └── GraphExecutionCreatedEvent inkrementuje current_cycle (= next_cycle)
               └── Dane z X.state_output są kopiowane do state_input nowego grafa
               └── scheduler uruchomi PLANNERA nowego grafa w kolejnym cyklu
```

- Replan **zawsze tworzy nowy `GraphExecution` z `parent=None`** — nigdy nie resetuje istniejącego (audit trail zachowany).
- Link do failed grafa poprzednika jest w `state_input.previous_attempt_id` — to dane audytowe, nie relacja strukturalna.
- `GraphExecutionStateInput` nowego grafa zawiera: `previous_attempt_id: X.id`, `prior_state_output: snapshot z X.state_output`.
- `current_cycle` inkrementowane w `GraphExecutionCreatedEvent` handlerze, **tylko gdy `parent_graph_execution_id=None`**.
- **Brak flagi "replanowalności"** — każdy FAILED rundy głównej idzie do replanu; jedynym ograniczeniem jest `max_planning_cycles`.

## 13. Scheduler — głupi orkiestrator

Scheduler działa w pętli. Każdy cykl:

```
1. Opróżnij INBOX
   └── dla każdego eventu → dispatch do handlera
       (handlery modyfikują stany agregatów i emitują nowe eventy do OUTBOX)

2. Przepisz OUTBOX → INBOX
   └── eventy wyprodukowane przez handlery trafiają do outbox →
       scheduler przenosi je do inbox na następny cykl

3. Gdy INBOX pusty i OUTBOX pusty → znajdź graf do uruchomienia
   └── kryteria (wszystkie muszą być spełnione):
       a) GraphExecution.status == PENDING
       b) GraphExecution.parent_graph_execution_id jest None LUB
          parent GraphExecution istnieje i jest w stanie PLANNING
          (sub-graf może startować gdy parent już czeka — równoległość)
       c) TaskExecution.status == IN_PROGRESS
       d) TaskExecution.current_cycle <= max_planning_cycles
   └── uruchom pierwszy node (PLANNER) tego GraphExecution
       └── emit GraphPlanningStartedEvent
```

**Scheduler NIE zna biznesu.** On tylko:
- przekazuje eventy (krok 1, 2),
- gdy nic się nie dzieje → sprawdza czy jest graf `PENDING` gotowy do startu i uruchamia jego PLANNERA (krok 3).

**Scheduler NIE wznawia parenta po sub-grafach** — to robi wyłącznie `SubGraphSettledEvent` (produkowany przez handler `GraphExecutionCompletedEvent`/`GraphExecutionFailedEvent` gdy query po `parent_graph_execution_id` zwróci wszystkie dzieci w stanie końcowym). Parent pozostaje w `PLANNING` (nie `PENDING`), więc scheduler i tak go nie podniesie w kroku 3.

**Scheduler NIE decyduje o replanie** — to robi handler `GraphExecutionFailedEvent` emitując `GraphExecutionCreatedEvent` z `parent=None`.

## 14. Pełen scenariusz end-to-end

```
User/System
    │
    ▼
Import z pliku / API Create
    │
    ▼
emit TaskExecutionCreatedEvent (current_cycle=0, max_planning_cycles=5)
    │
    ▼
Handler:
    └── tworzy GraphExecution G1 (parent_graph_execution_id=None)
    └── emit GraphExecutionCreatedEvent
         └── current_cycle=1, TaskExecution → IN_PROGRESS
    │
    ▼
Scheduler (INBOX pusty): znajduje G1 PENDING → uruchom PLANNERA
    │
    ▼
PLANNER G1:
    ├── decyduje: plan bezpośredni (exec) LUB spawn sub-grafu
    │
    ├── Scenariusz A (plan bezpośredni):
    │   └── emit GraphPlannedEvent → G1.EXECUTING
    │       └── AGENT/TOOLS → emit GraphNodeExecutionCompletedEvent
    │           └── G1.VERIFYING → VERIFIER
    │               ├── OK → GraphExecutionCompletedEvent → G1.COMPLETED
    │               │        └── parent=None → TaskExecutionCompletedEvent → COMPLETED
    │               └── FAIL → GraphExecutionFailedEvent → G1.FAILED
    │                        └── handler: next_cycle=2 <=5 → GraphExecutionCreatedEvent(parent=None, goal="replan") → cykl #2
    │                        └── state_input nowego grafa zawiera previous_attempt_id=G1
    │
    └── Scenariusz B (spawn sub-grafu do analizy):
        └── emit GraphSpawnedEvent(goal="analiza X")
            └── tworzy GraphExecution G2 (parent_graph_execution_id=G1)
            └── G1 nadal w PLANNING (scheduler nie rusza — ma niezakonczone dzieci)
                └── scheduler uruchamia G2 (PLANNER → ... → VERIFIER)
                    ├── G2.COMPLETED → wynik w G2.state_output
                    └── po ostatnim dziecku → emit SubGraphSettledEvent(parent=G1, child_results=[...])
                        └── child_results zapisane w G1.state_input
                        └── G1 → PLANNING (resume)
                        └── PLANNER G1 podejmuje decyzję: exec / kolejny spawn / fail
```

## 15. Podsumowanie zmian vs V1

| Luka V1 | Naprawa V2 |
|---------|-----------|
| Replan i sub-graf nieodróżnialne — V1 rysował replan B z `parent=A` | Replan = `parent=None` (nowy graf główny), sub-graf = `parent=<id>`. Link audytowy w `state_input.previous_attempt_id` (§2, §8.1) |
| "nowy/lub ten sam" GraphExecution przy replanie | Zawsze nowy `GraphExecution` z `parent=None`; maszyna stanów bez powrotu z FAILED (§8.2, §12) |
| Brak mechanizmu wznowienia rodzica po sub-grafie | `SubGraphSettledEvent` jako sygnał wznowienia; "parent czeka" wyprowadzane query'm po `parent_graph_execution_id` bez sztucznego stanu (§8.2, §10.2, §11.1, §13) |
| Brak obsługi FAILED sub-grafu | Trzy jawnie zdefiniowane decyzje PLANNERA rodzica (§11.3) |
| Agent/Tools równoległe vs liniowe | Pipeline liniowy z `order`, AGENT i TOOLS opcjonalne (§9.2) |
| Nieokreślone inkrementowanie cycle | Inkrementacja gdy `parent_graph_execution_id=None`; sub-grafy nie inkrementują; pierwsza runda = 1 (§7.3, §10.2) |
| Brak `GraphExecutionCreatedEvent` w katalogu | Pełen katalog eventów (§10) |
| Brak triggera CREATED→IN_PROGRESS | `TaskExecutionCreatedEvent` handler tworzy pierwszy graf i ustawia IN_PROGRESS (§7.2, §10.1) |
| Błędna numeracja §12.x | Spójna numeracja (§9.3) |
| TaskExecution.skills vs Workflow.skills niejasne | `TaskExecution.skills` to frozen snapshot; `AgentSkillExecution` to archive (§6) |
| WAITING "nigdzie nie zapisywany" | Jawny stan w maszynie (§8.2) |
| Brak limitu rekurencji sub-grafów | `max_subgraph_depth` (§11.4) |
| Sub-grafy mogły replanować wewnętrznie (niejednoznaczne) | Sub-grafy NIE replanują — failure bubluje do parent PLANNER (§11.3) |
| GraphNodeTransitionExecution jako "future concept" | Transitions są pełnoprawną częścią V2 (§16); SEQUENCE/CONDITIONAL/PARALLEL/JOIN/LOOP/ERROR_HANDLER/TIMEOUT/DEFAULT |
| TaskExecution.skills jako embedded List[SkillSnapshot] | TaskExecution to osobna tabela `TaskExecutionSkill` (§6.1); brak embedded snapshotów |
| hash na TaskExecution | Usunięty — deduplikacja poza zakresem V2 |
| Session.goal istniał | Usunięty — cel zadania w TaskExecution.description |
| AgentConfigExecution tylko dla AGENT | AgentConfigExecution dla wszystkich nodów LLM (PLANNER + AGENT) (§4) |
| Eventy bez określonego ownershipu | Każdy event należy do emitenta (§10) — GraphExecution*, GraphNodeExecution*, TaskExecution* |
| Session bez statusu | Dodany status OPEN/CLOSED (§3) |

---

## 16. GraphNodeTransitionExecution — krawędzie grafu

Domyślny pipeline V2 jest liniowy (`order`). Dla przypadków wymagających nie-linearnego przepływu routing między nodami definiowany jest przez `GraphNodeTransitionExecution`. Każda tranzycja łączy `source_node_execution_id` → `target_node_execution_id` i określa typ przejścia.

### 16.1 Typy krawędzi

| Typ | Kto podejmuje decyzję | Zachowanie |
|-----|----------------------|------------|
| **SEQUENCE** | Domyślna (automat) | Przejście do następnego noda wg `order`. Brak decyzji — pipeline liniowy. |
| **CONDITIONAL** | AGENT / TOOLS (wynik noda) | Wynik noda zawiera dane dla ewaluacji `condition_expression`. Scheduler ewaluuje warunek na outputcie → różne targety dla `true` / `false`. Np. AGENT zwraca `{"quality": 0.9}` → jeśli `>0.8` idź do VERIFIER, inaczej do PLANNER (popraw). |
| **PARALLEL** | PLANNER (`GraphPlannedEvent`) | PLANNER określa fork — wiele nodów AGENT/TOOLS uruchamianych współbieżnie w ramach tego samego `GraphExecution`. Różnica od sub-grafów (§11): to nody w bieżącym grafie, nie osobne `GraphExecution`. |
| **JOIN** | Automat (po PARALLEL) | Sync point. Scheduler nie rusza następnego noda, dopóki wszystkie wejściowe nody (z PARALLEL) nie skończą. Połączone wyniki trafiają do `state_input` target noda. |
| **LOOP** | PLANNER / AGENT (wynik noda) | Powrót do poprzedniego noda (np. PLANNER) z `state_input` wzbogaconym o wyniki iteracji. Zabezpieczony `max_iterations`. Jeśli przekroczony → VERIFIER z błędem (graf kończy się FAILED). |
| **ERROR_HANDLER** | Scheduler (automat po FAILED) | Gdy node zakończy się `GraphNodeExecutionFailedEvent`, scheduler sprawdza czy istnieje krawędź `ERROR_HANDLER` → przekierowuje do noda obsługi błędów. Jeśli brak → `GraphExecutionFailedEvent` (standardowy fail). |
| **TIMEOUT** | Scheduler (po przekroczeniu czasu) | Analogicznie do ERROR_HANDLER, triggerowany przez timeout noda. |
| **DEFAULT** | Fallback | Gdy żaden warunek CONDITIONAL nie pasuje. |

### 16.2 Przepływ decyzyjny

```
GraphNodeExecution zakończony (COMPLETED / FAILED / TIMEOUT)
    │
    ▼
Scheduler pobiera outgoing transitions dla tego noda
    │
    ├── Brak tranzycji → koniec pipeline (VERIFIER → GraphExecutionCompletedEvent)
    │
    ├── SEQUENCE → uruchom następny node wg order
    ├── CONDITIONAL → ewaluuj condition_expression na result; wybierz target
    ├── PARALLEL → uruchom wszystkie targety współbieżnie; czekaj na JOIN
    ├── LOOP → sprawdź max_iterations; jeśli nie przekroczone → wróć do source noda
    ├── ERROR_HANDLER → (tylko przy FAILED) przekieruj do error handler noda
    ├── TIMEOUT → (tylko przy TIMEOUT) przekieruj do timeout handler noda
    └── DEFAULT → fallback gdy CONDITIONAL nie matchuje
```

### 16.3 Relacja z sub-grafami

**PARALLEL (nody w tym samym grafie) ≠ spawn sub-grafów (osobne GraphExecution):**

| Aspekt | PARALLEL | Sub-graf |
|--------|----------|----------|
| Scope | W ramach bieżącego `GraphExecution` | Nowy `GraphExecution` z własnym PLANNERem |
| Pipeline | Tylko nody AGENT/TOOLS (współbieżne) | Pełny pipeline PLANNER→...→VERIFIER |
| Rezultat | Wyniki trafiają do JOIN → następny node | Wyniki trafiają do `SubGraphSettledEvent` → parent PLANNER |
| Użycie | Współbieżne tool calls / agent calls | Niezależne pod-zadania, human-in-the-loop, analiza |

### 16.4 Powiązane encje

- `GraphNodeTransitionExecution` — tranzycja w ramach wykonania (runtime)
- `GraphNodeTransitionDefinition` — szablon tranzycji (definicja, wielokrotnego użytku)
- `GraphDefinition` / `GraphNodeDefinition` — statyczne definicje grafów i nodów, z których runtime instantuje `GraphExecution` / `GraphNodeExecution`

---

## 17. Message — wspólny value object dla komunikacji

W domenie wszystkie wiadomości (komendy, eventy, zapytania) używają wspólnego value object:

```
Message
 ├── id: str              # UUID / korrelation ID
 ├── type: str            # nazwa typu wiadomości
 ├── payload: dict        # treść
 ├── occurred_at: datetime
 └── schema_version: int
```

- `Message` jest value objectem platformy (`shell.domain.platform`), dostępnym dla wszystkich bounded contextów.
- Mechanizm Envelope (routing, gwarancja dostarczenia, deadletter) jest implementacją w warstwie **infrastruktury**, nie domeny. Domenowy handler pracuje na `Message`, nie na `Envelope`.
- Scheduler (patrz §13) operuje na `Message` — inbox/outbox to lista `Message` do przetworzenia.

---

## 18. Inne mechanizmy (ortogonalne)

Poniższe koncepty istnieją w kodzie i są **ortogonalne** względem modelu V2. Nie wpływają na maszynę stanów TaskExecution, GraphExecution, GraphNodeExecution, ani na pętlę replanowania.

### 18.1 RAG (Retrieval-Augmented Generation)

`RagDocument` i `RagChunk` z embeddingiem służą do wyszukiwania semantycznego (`SearchSimilarQuery`). Używane przez AGENT/PLANNER jako źródło wiedzy.

### 18.2 RunnerConfig

`RunnerConfig` przechowuje konfiguracje runnerów (np. `kind: "python"`, `body: {"script": "..."}`). Używane przez TOOLS do deterministycznego wykonania.

> **Zasada:** Powyższe mechanizmy są rozszerzeniami — mogą być dodawane warstwowo bez wpływu na rdzeń V2.
