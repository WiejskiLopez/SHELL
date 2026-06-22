# Domain Simulation — SHELL V3

> 10 scenariuszy orkiestracji domeny na podstawie `DOMAINV3.md`.
> Każdy scenariusz = pełny event trace. Eventy oznaczone **✳**  → brak w katalogu DOMAINV3 — trzeba dodać.

---

## S1. Happy Path — proste zadanie, jedna runda, sukces

**Context:** Task `"Dodaj testy jednostkowe do modułu X"`. PLANNER tworzy plan bezpośredni. AGENT wykonuje. VERIFIER akceptuje.

```
S1.1  → TaskExecutionCreatedEvent(task_execution_id="T1", description="Dodaj testy jednostkowe do modułu X",
         skills=[{source:"session.user", payload:{...}}, {source:"workflow.architecture", payload:{...}}])
         ├─ Handler: kopiuje skille → TaskExecutionSkill[] (2 wiersze)
         ├─ Handler: tworzy GraphExecution G1 (parent=None, depth=0)
         └─ Handler: emit GraphExecutionCreatedEvent(graph_execution_id="G1", task_execution_id="T1",
              parent_graph_execution_id=None, goal="Dodaj testy...", depth=0)

S1.2  → GraphExecutionCreatedEvent(G1, T1, parent=None, goal="...", depth=0)
         ├─ Handler: parent=None → current_cycle = 1
         ├─ Handler: goal → GraphExecutionStateInput(G1)
         ├─ Handler: emituje TaskExecutionStartedEvent → T1 → IN_PROGRESS
         └─ TaskExecution: status=IN_PROGRESS, current_cycle=1

S1.3  [Scheduler step 4: inbox/outbox puste → znajduje G1 PENDING]
      → GraphPlanningStartedEvent(graph_execution_id="G1")
         └─ G1 → PLANNING

S1.4  [Scheduler step 4: G1.PLANNING → uruchom PLANNER]
      → GraphNodeExecutionStartedEvent(node_id="N1", role="PLANNER")
         └─ N1 → RUNNING

S1.5  [PLANNER wykonuje pracę — LLM analizuje zadanie, produkuje plan bezpośredni]
      → GraphNodeExecutionCompletedEvent(node_id="N1", role="PLANNER",
           result={"stage":"direct","plan":{"agents":[{"role":"AGENT","prompt":"..."}],
           "tools":[{"kind":"python","script":"pytest"}]}})
         ├─ Handler: result → GraphNodeStateOutput(N1)
         ├─ Handler: tworzy GraphNodeExecution[] wg planu (N2=AGENT, N3=TOOLS, N4=VERIFIER)
         ├─ Handler: tworzy SEQUENCE krawędzie N1→N2, N2→N3, N3→N4
         └─ Handler: emit GraphPlannedEvent(graph_execution_id="G1", plan={...})

S1.6  → GraphPlannedEvent(G1, plan)
         ├─ Handler: plan → GraphExecutionStateInput(G1)
         └─ G1 → EXECUTING

S1.7  [Scheduler decision layer: N1 ma outgoing SEQUENCE N1→N2]
      → TransitionTakenEvent(transition_id="T_seq1", source_node_id="N1", target_node_id="N2")
         ├─ Handler: start N2
         └─ emit GraphNodeExecutionStartedEvent(node_id="N2", role="AGENT")

S1.8  → GraphNodeExecutionStartedEvent(N2, AGENT) → N2 → RUNNING

S1.9  [AGENT wykonuje — LLM z skillami z TaskExecutionSkill]
      → GraphNodeExecutionCompletedEvent(node_id="N2", role="AGENT",
           result={"files_written":["test_x.py"], "summary":"Testy utworzone"})
         ├─ Handler: result → GraphNodeStateOutput(N2)
         └─ N2 → COMPLETED

S1.10 [Scheduler decision: N2 → SEQUENCE N2→N3]
      → TransitionTakenEvent("T_seq2", N2, N3)
         └─ emit GraphNodeExecutionStartedEvent(node_id="N3", role="TOOLS")

S1.11 → GraphNodeExecutionStartedEvent(N3, TOOLS) → N3 → RUNNING

S1.12 [TOOLS wykonuje deterministycznie `pytest`]
      → GraphNodeExecutionCompletedEvent(node_id="N3", role="TOOLS",
           result={"exit_code":0, "output":"42 passed"})
         ├─ result → GraphNodeStateOutput(N3)
         └─ N3 → COMPLETED

S1.13 [Scheduler decision: N3 → SEQUENCE N3→N4]
      → TransitionTakenEvent("T_seq3", N3, N4)
         └─ emit GraphNodeExecutionStartedEvent(node_id="N4", role="VERIFIER")

S1.14 → GraphNodeExecutionStartedEvent(N4, VERIFIER) → N4 → RUNNING

S1.15 [VERIFIER ocenia — porównuje output z goal]
      → GraphNodeExecutionCompletedEvent(node_id="N4", role="VERIFIER",
           result={"verdict":"PASS","summary":"Wszystkie testy przechodzą"})
         ├─ result → GraphNodeStateOutput(N4)
         ├─ Handler: role=VERIFIER + verdict=PASS → emit GraphExecutionCompletedEvent(G1)
         └─ N4 → COMPLETED

S1.16 → GraphExecutionCompletedEvent(graph_execution_id="G1", verifier_result={"verdict":"PASS",...})
         ├─ G1 → COMPLETED
         ├─ Handler: parent=None → emit TaskExecutionCompletedEvent
         └─ verifier_result → GraphExecutionStateOutput(G1)

S1.17 → TaskExecutionCompletedEvent(task_execution_id="T1", output={"verdict":"PASS","cycles":1})
         ├─ T1 → COMPLETED
         └─ Handler: output → WorkflowStateInput(workflow_id=T1.workflow_id)

=== WYNIK: TaskExecution.COMPLETED, 1 runda, 4 nody, 0 błędów ===
```

---

## S2. Replan Success — pierwsza runda FAIL, replan OK

**Context:** AGENT pisze błędny kod. VERIFIER failuje. Replan (runda #2) poprawia.

```
S2.1  → TaskExecutionCreatedEvent(T2, "Zaimplementuj cache LRU", skills=[...])
S2.2  → GraphExecutionCreatedEvent(G1, T2, parent=None, goal="...", depth=0)
         └─ current_cycle=1, T2→IN_PROGRESS
S2.3  → GraphPlanningStartedEvent(G1) → G1.PLANNING
S2.4  → GraphNodeExecutionStartedEvent(N1, PLANNER) → N1.RUNNING
S2.5  → GraphNodeExecutionCompletedEvent(N1, PLANNER, result={"stage":"direct","plan":{...}})
         └─ Handler: emit GraphPlannedEvent(G1, plan)
S2.6  → GraphPlannedEvent(G1) → G1.EXECUTING
S2.7  [AGENT N2 wykonuje — popełnia błędy]
      → GraphNodeExecutionCompletedEvent(N2, AGENT, result={"files":["lru.py"],
           "implementation":"brak thread-safety"})
S2.8  [TOOLS N3 — testy failują]
      → GraphNodeExecutionCompletedEvent(N3, TOOLS, result={"exit_code":1,"output":"3 failed"})
S2.9  [VERIFIER N4 — ocena negatywna]
      → GraphNodeExecutionCompletedEvent(N4, VERIFIER,
           result={"verdict":"FAIL","reason":"Testy nie przechodzą, brak thread-safety"})
         ├─ Handler: role=VERIFIER + verdict=FAIL → emit GraphExecutionFailedEvent(G1)

S2.10 → GraphExecutionFailedEvent(graph_execution_id="G1",
            reason="Testy nie przechodzą, brak thread-safety")
         ├─ G1 → FAILED (nierewersybilne)
         ├─ Handler: parent=None → sprawdź replan
         │   ├─ next_cycle = 1 + 1 = 2
         │   ├─ 2 ≤ max_planning_cycles (5) → OK
         │   └─ emit GraphExecutionCreatedEvent(task_execution_id="T2",
         │        parent_graph_execution_id=None, goal="replan: Zaimplementuj cache LRU",
         │        depth=0)
         └─ G1.reason → GraphExecutionStateOutput(G1)

S2.11 → GraphExecutionCreatedEvent(G2, T2, parent=None, goal="replan: ...", depth=0)
         ├─ Handler: parent=None → current_cycle = 2
         ├─ Handler: kopiuje G1.GraphExecutionStateOutput → G2.GraphExecutionStateInput
         │   (previous_attempt_id=G1, prior_state_output={verdict:FAIL, reason:...})
         └─ T2: current_cycle=2 (zostaje IN_PROGRESS)

S2.12 [Scheduler: G2 PENDING]
      → GraphPlanningStartedEvent(G2) → G2.PLANNING

S2.13 [PLANNER G2 — uwzględnia powód porażki, poprawia strategię]
      → GraphNodeExecutionStartedEvent(N5, PLANNER)
      → GraphNodeExecutionCompletedEvent(N5, PLANNER,
           result={"stage":"direct","plan":{"agents":[{"role":"AGENT",
           "prompt":"Użyj threading.Lock w implementacji"}]}})
         └─ emit GraphPlannedEvent(G2)

S2.14 → GraphPlannedEvent(G2) → G2.EXECUTING
S2.15 [AGENT N6 — pisze poprawny kod]
      → GraphNodeExecutionCompletedEvent(N6, AGENT, result={"files":["lru.py"],
           "implementation":"thread-safe LRU z threading.Lock"})
S2.16 [TOOLS N7 — testy OK]
      → GraphNodeExecutionCompletedEvent(N7, TOOLS, result={"exit_code":0,"output":"all passed"})
S2.17 [VERIFIER N8 — PASS]
      → GraphNodeExecutionCompletedEvent(N8, VERIFIER, result={"verdict":"PASS","summary":"OK"})
         └─ emit GraphExecutionCompletedEvent(G2)

S2.18 → GraphExecutionCompletedEvent(G2, verifier_result={"verdict":"PASS",...})
         ├─ G2 → COMPLETED
         └─ parent=None → emit TaskExecutionCompletedEvent(T2)

S2.19 → TaskExecutionCompletedEvent(T2, output={"verdict":"PASS","cycles":2,"replan_reason":"thread-safety"})
         └─ T2 → COMPLETED

=== WYNIK: TaskExecution.COMPLETED, 2 rundy, FAILED replan zadziałał poprawnie ===
```

---

## S3. Exhausted — limit rund przekroczony

**Context:** Zadanie wymagające 6 prób. `max_planning_cycles=3`. Po 3 rundzie FAIL → EXHAUSTED.

```
S3.1-9  [Jak S2 — pierwsza runda, VERIFIER fail]
        → GraphExecutionFailedEvent(G1, "Błąd implementacji")
        → replan: G2 created, current_cycle=2
        → [Druga runda, też FAIL]
        → GraphExecutionFailedEvent(G2, "Nadal błędy")
        → replan: G3 created, current_cycle=3
        → [Trzecia runda, też FAIL]
        → GraphExecutionFailedEvent(G3, "Nieudana trzecia próba")
         ├─ Handler: parent=None → next_cycle = 3 + 1 = 4
         ├─ 4 > max_planning_cycles (3) → EXHAUSTED
         └─ emit TaskExecutionExhaustedEvent(task_execution_id="T3",
              current_cycle=3, max_planning_cycles=3)

S3.10 → TaskExecutionExhaustedEvent(T3, current_cycle=3, max=3)
         └─ T3 → EXHAUSTED (nierewersybilne)

=== WYNIK: TaskExecution.EXHAUSTED, 3 rundy zużyte, brak kolejnego replanu ===
```

---

## S4. Sub-graph Success — PLANNER spawnuje 2 sub-grafy, oba OK, parent kontynuuje

**Context:** PLANNER dzieli zadanie na 2 niezależne pod-zadania. Spawnuje 2 sub-grafy. Parent czeka. Oba kończą się OK. Parent resume i kończy sukcesem.

```
S4.1-3  Task T4 utworzone, G1 (parent=None) w PLANNING, PLANNER N1 uruchomiony

S4.4  → GraphNodeExecutionCompletedEvent(N1, PLANNER,
           result={"stage":"spawn","spawns":[
             {"goal":"Przeanalizuj moduł auth"},
             {"goal":"Przeanalizuj moduł payments"}
           ]})
         ├─ Handler: result ma stage=spawn → NIE emituje GraphPlannedEvent
         └─ Handler: dla każdego spawn → tworzy GraphExecution z parent=G1

S4.5  → GraphSpawnedEvent(parent_graph_execution_id="G1", child_graph_execution_id="G2",
           goal="Przeanalizuj moduł auth", depth=1)
         └─ Handler: tworzy G2 (parent=G1, depth=1); goal → G2.GraphExecutionStateInput
         └─ G1 zostaje w PLANNING (niezakonczone dzieci)

S4.6  → GraphSpawnedEvent(parent="G1", child="G3", goal="Przeanalizuj moduł payments", depth=1)
         └─ Handler: tworzy G3 (parent=G1, depth=1)

S4.7  [Scheduler: G2 PENDING + parent G1 w PLANNING → OK]
      → GraphPlanningStartedEvent(G2) → G2.PLANNING

S4.8  [Scheduler: G3 PENDING + parent G1 w PLANNING → OK — współbieżnie!]
      → GraphPlanningStartedEvent(G3) → G3.PLANNING

S4.9-14 [G2 wykonuje swój pipeline: PLANNER→AGENT→VERIFIER → COMPLETED]
        → GraphExecutionCompletedEvent(G2, verifier_result={"verdict":"PASS","analysis":"auth używa JWT"})
         ├─ G2 → COMPLETED
         ├─ Handler: parent=G1 → query: wszystkie dzieci G1 w stanie końcowym?
         │   ├─ G2 = COMPLETED ✓
         │   └─ G3 = jeszcze PLANNING ✗ → NIE emituj SubGraphSettledEvent

S4.15-20 [G3 wykonuje swój pipeline → COMPLETED]
         → GraphExecutionCompletedEvent(G3, verifier_result={"verdict":"PASS","analysis":"payments używa Stripe"})
         ├─ G3 → COMPLETED
         └─ Handler: parent=G1 → query: wszystkie dzieci G1 w stanie końcowym?
             ├─ G2 = COMPLETED ✓
             └─ G3 = COMPLETED ✓ → emit SubGraphSettledEvent

S4.21 → SubGraphSettledEvent(parent_graph_execution_id="G1",
            child_results=[
              {graph_execution_id:"G2", status:"COMPLETED", result:{...}},
              {graph_execution_id:"G3", status:"COMPLETED", result:{...}}
            ])
         ├─ Handler: children_results → GraphExecutionStateInput(G1)
         └─ G1 pozostaje w PLANNING → scheduler może wznowić PLANNERA z wynikami

S4.22 [Scheduler: G1.PLANNING + GraphExecutionStateInput ma children_results]
      → PLANNER N1 wznawiany (ten sam node? nowy node?)  
      [Założenie: PLANNER resume = nowy GraphNodeExecution z enriched state_input]
      → GraphNodeExecutionStartedEvent(N1b, PLANNER)  // re-entered PLANNER

S4.23 → GraphNodeExecutionCompletedEvent(N1b, PLANNER,
           result={"stage":"direct","plan":{
             "incorporating_results":["auth: JWT ok","payments: Stripe ok"],
             "agents":[{"role":"AGENT","prompt":"Zintegruj moduły na podstawie analiz"}]}})
         └─ Handler: stage=direct → emit GraphPlannedEvent(G1)

S4.24 → GraphPlannedEvent(G1, plan) → G1.EXECUTING
S4.25-30 [AGENT→TOOLS→VERIFIER w G1 → COMPLETED]
         → GraphExecutionCompletedEvent(G1, verifier_result={"verdict":"PASS","summary":"Integracja OK"})
         └─ parent=None → emit TaskExecutionCompletedEvent(T4)

S4.31 → TaskExecutionCompletedEvent(T4, output={...})

=== WYNIK: TaskExecution.COMPLETED, 1 runda główna + 2 sub-grafy, wszystkie OK ===
```

---

## S5. Sub-graph FAIL, Parent Adapts

**Context:** PLANNER spawnuje sub-graf. Child returns FAIL. Parent PLANNER akceptuje porażkę, dostosowuje plan, kontynuuje do sukcesu.

```
S5.1-5  [Jak S4 — PLANNER spawnuje sub-graf G2]

S5.6-10 [G2 wykonuje pipeline → VERIFIER fail]
        → GraphExecutionFailedEvent(G2, reason="Moduł nie istnieje")
         ├─ G2 → FAILED
         └─ Handler: parent=G1 → query: wszystkie dzieci końcowe?
             └─ G2 jedyne dziecko, FAILED = stan końcowy → emit SubGraphSettledEvent

S5.11 → SubGraphSettledEvent(parent_graph_execution_id="G1",
            child_results=[
              {graph_execution_id:"G2", status:"FAILED",
               result:{"reason":"Moduł nie istnieje"}}
            ])
         ├─ children_results → GraphExecutionStateInput(G1)
         └─ G1 → PLANNING (resume)

S5.12 [PLANNER G1 resume — widzi że child FAILED, decyzja: "Akceptuj porażkę i dostosuj plan"]
      → GraphNodeExecutionStartedEvent(N1b, PLANNER)
      → GraphNodeExecutionCompletedEvent(N1b, PLANNER,
           result={"stage":"direct","plan":{
             "note":"Moduł X nie istnieje — pomijamy",
             "agents":[{"role":"AGENT","prompt":"Kontynuuj bez modułu X"}]}})
         └─ emit GraphPlannedEvent(G1)

S5.13 → GraphPlannedEvent(G1) → G1.EXECUTING
S5.14-18 [AGENT→VERIFIER → COMPLETED]
         → GraphExecutionCompletedEvent(G1) → TaskExecutionCompletedEvent(T5)

=== WYNIK: TaskExecution.COMPLETED, parent zaakceptował FAIL sub-grafu i dostosował ===
```

---

## S6. Sub-graph Fatal FAIL, Parent Fails

**Context:** Sub-graf fail jest blokujący. PLANNER decyduje: "Fail rodzica".

```
S6.1-11 [Jak S5 — sub-graf G2 FAILED, SubGraphSettledEvent do G1]

S6.12 [PLANNER G1 resume — analizuje children_results]
      → GraphNodeExecutionStartedEvent(N1b, PLANNER)
      → GraphNodeExecutionCompletedEvent(N1b, PLANNER,
           result={"stage":"abort",
             "reason":"Kluczowy moduł auth nie istnieje — nie można kontynuować"})
         └─ Handler: stage=abort → emit GraphExecutionFailedEvent(G1)

S6.13 → GraphExecutionFailedEvent(G1, reason="Kluczowy moduł auth nie istnieje")
         ├─ G1 → FAILED
         ├─ Handler: parent=None → next_cycle=2 ≤ max → replan
         └─ emit GraphExecutionCreatedEvent(T6, parent=None, goal="replan: ...")
            (nowa runda próbuje innego podejścia)

S6.14 → GraphExecutionCreatedEvent(G3, T6, parent=None, goal="replan: ...", depth=0)
         └─ current_cycle=2, G3.PENDING

[Scheduler uruchamia G3 → może dalej replanować, succeed, lub exhaust]

=== WYNIK: Parent zdecydował FAIL na podstawie krytycznego błędu sub-grafu.
           Replan tworzy nową rundę. ===
```

---

## S7. CONDITIONAL Transition — AGENT result decyduje o routingu

**Context:** AGENT wykonuje, ale quality output jest niskie. CONDITIONAL edge kieruje z powrotem do PLANNERA zamiast do VERIFIER.

```
S7.1-6  [PLANNER N1 → direct plan → GraphPlannedEvent(G1) → G1.EXECUTING]

S7.7  [Scheduler decision: N1 outgoing edge = CONDITIONAL zamiast SEQUENCE]
      PLANNER zdefiniował:
        - CONDITIONAL: condition_expression="result.quality > 0.8",
          target_node_execution_id="VERIFIER_N4"
        - DEFAULT: target_node_execution_id="PLANNER_N1b"  // fallback — poproś PLANNER o poprawę

S7.8  → TransitionTakenEvent("T_cond1", N1, N2)  [SEQUENCE/start AGENT]
      → GraphNodeExecutionStartedEvent(N2, AGENT) → N2.RUNNING

S7.9  → GraphNodeExecutionCompletedEvent(N2, AGENT,
           result={"files":["draft.py"],"quality":0.45})
         ├─ result → GraphNodeStateOutput(N2)
         └─ N2 → COMPLETED

S7.10 [Scheduler decision layer: N2 ma outgoing CONDITIONAL]
      → TransitionConditionEvaluatedEvent(transition_id="T_cond2", source_node_id="N2",
           condition_expression="result.quality > 0.8", condition_result=false)
         └─ condition_result=false → pomijamy CONDITIONAL

S7.11 [Scheduler: następny edge to DEFAULT]
      → TransitionTakenEvent("T_default", N2, N1b)  // PLANNER re-entry
         └─ emit GraphNodeExecutionStartedEvent(node_id="N1b", role="PLANNER")

S7.12 → GraphNodeExecutionStartedEvent(N1b, PLANNER) → N1b.RUNNING

S7.13 [PLANNER N1b — dostał output AGENT z quality=0.45, poprawia strategię]
      → GraphNodeExecutionCompletedEvent(N1b, PLANNER,
           result={"stage":"direct","plan":{
             "note":"Poprawiono prompt dla AGENT",
             "agents":[{"role":"AGENT","prompt":"Popraw kod — quality musi być > 0.8"}]}})
         └─ emit GraphPlannedEvent(G1)

S7.14 → GraphPlannedEvent(G1, plan_v2) → G1 pozostaje EXECUTING
S7.15 [SEQUENCE N1b→N2b (nowy AGENT)]
      → GraphNodeExecutionStartedEvent(N2b, AGENT)
      → GraphNodeExecutionCompletedEvent(N2b, AGENT,
           result={"files":["draft_v2.py"],"quality":0.92})

S7.16 [Scheduler decision: quality=0.92 > 0.8 → CONDITIONAL selected]
      → TransitionConditionEvaluatedEvent("T_cond3", N2b, "result.quality > 0.8", true)
      → TransitionTakenEvent("T_cond3", N2b, N4)  // target = VERIFIER
         └─ emit GraphNodeExecutionStartedEvent(N4, VERIFIER)

S7.17 [VERIFIER → PASS]
      → GraphExecutionCompletedEvent(G1) → TaskExecutionCompletedEvent(T7)

=== WYNIK: CONDITIONAL zadziałał — niska quality → DEFAULT → PLANNER poprawka.
           Wysoka quality → CONDITIONAL → VERIFIER. Sukces po jednej iteracji poprawki. ===
```

---

## S8. LOOP Transition — wielokrotna iteracja PLANNER→AGENT→VERIFIER

**Context:** PLANNER definiuje LOOP edge: jeśli VERIFIER fail powtarzalny → wróć do PLANNERA (max 3 iteracje).

```
S8.1-5  [PLANNER N1, GraphPlannedEvent(G1), G1.EXECUTING]

        PLANNER zdefiniował:
          - SEQUENCE: N1→N2 (AGENT), N2→N3 (VERIFIER)
          - LOOP: N3→N1, max_iterations=3

S8.6-9  [AGENT N2 wykonuje → COMPLETED]
        [VERIFIER N3 → FAIL]
        → GraphNodeExecutionCompletedEvent(N3, VERIFIER,
             result={"verdict":"FAIL","reason":"Niepełna implementacja"})

S8.10 [Scheduler decision: N3 ma outgoing LOOP]
      → TransitionLoopedEvent(transition_id="T_loop", source_node_id="N3", iteration=1)
         ├─ Handler: iteration=1 ≤ max=3 → wznów PLANNER
         └─ emit GraphNodeExecutionStartedEvent(node_id="N1b", role="PLANNER")
            (GraphNodeStateInput(N1b) wzbogacony o reason="Niepełna implementacja")

S8.11 → GraphNodeExecutionStartedEvent(N1b, PLANNER) → N1b.RUNNING
      → GraphNodeExecutionCompletedEvent(N1b, PLANNER,
           result={"stage":"direct","plan":{"note":"Iteracja 2 — uzupełniamy braki"}})
         └─ emit GraphPlannedEvent(G1)

S8.12-15 [SEQUENCE N1b→N2b(AGENT)→N3b(VERIFIER)]
         [VERIFIER znowu FAIL]
         → GraphNodeExecutionCompletedEvent(N3b, VERIFIER,
              result={"verdict":"FAIL","reason":"Nadal luki"})

S8.16 → TransitionLoopedEvent("T_loop", N3b, iteration=2)
         └─ Handler: 2 ≤ 3 → jeszcze raz PLANNER

S8.17-20 [Trzecia iteracja: PLANNER N1c → AGENT N2c → VERIFIER N3c]
         [VERIFIER FAIL po raz trzeci]
         → GraphNodeExecutionCompletedEvent(N3c, VERIFIER,
              result={"verdict":"FAIL","reason":"Brak postępu po 3 iteracjach"})

S8.21 [Scheduler decision: N3c → LOOP]
      → TransitionLoopedEvent("T_loop", N3c, iteration=3)
         ├─ Handler: iteration=3 ≥ max=3 → NIE wznawiaj
         └─ emit GraphExecutionFailedEvent(G1, reason="LOOP exhausted po 3 iteracjach")

S8.22 → GraphExecutionFailedEvent(G1, "LOOP exhausted")
         ├─ G1 → FAILED
         └─ Handler: parent=None → replan (nowa runda G4)

=== WYNIK: LOOP działał 3 iteracje, po przekroczeniu max → FAIL → replan ===
```

---

## S9. ERROR_HANDLER Transition — node fail łapany przez handler

**Context:** TOOLS node crashuje. ERROR_HANDLER edge przechwytuje → uruchamia fallback VERIFIER, który odnotowuje błąd ale nie failuje całego grafu.

```
S9.1-7  [PLANNER N1 → GraphPlannedEvent(G1) → G1.EXECUTING]
        [SEQUENCE: N1→N2(AGENT)→N3(TOOLS)]
        [ERROR_HANDLER edge zdefiniowany z N3 → N4_err (specjalny VERIFIER)]

S9.8  → GraphNodeExecutionStartedEvent(N3, TOOLS) → N3.RUNNING

S9.9  [TOOLS crash — np. brak narzędzia w środowisku]
      → GraphNodeExecutionFailedEvent(node_id="N3", role="TOOLS",
           error="RuntimeError: brak narzędzia 'pytest' w PATH")
         ├─ error → GraphNodeStateOutput(N3)
         └─ N3 → FAILED

S9.10 [Scheduler decision: N3.FAILED + ma outgoing ERROR_HANDLER]
      → TransitionErrorHandledEvent(transition_id="T_err", failed_node_id="N3",
           handler_node_id="N4_err")
         └─ Handler: przekieruj do N4_err zamiast failować graf
         └─ emit GraphNodeExecutionStartedEvent(node_id="N4_err", role="VERIFIER")

S9.11 → GraphNodeExecutionStartedEvent(N4_err, VERIFIER) → N4_err.RUNNING

S9.12 [N4_err — VERIFIER z adnotacją o błędzie TOOLS]
      → GraphNodeExecutionCompletedEvent(N4_err, VERIFIER,
           result={"verdict":"PASS_WITH_WARNINGS",
             "warnings":["TOOLS node N3 failed: brak pytest — testy nieuruchomione"],
             "verdict_justification":"AGENT dostarczył poprawny kod mimo braku testów"})
         ├─ Handler: verdict=PASS_WITH_WARNINGS → graph może być COMPLETED
         └─ emit GraphExecutionCompletedEvent(G1)

S9.13 → GraphExecutionCompletedEvent(G1, verifier_result={...})
         └─ parent=None → emit TaskExecutionCompletedEvent(T9)

=== WYNIK: ERROR_HANDLER zadziałał — TOOLS crash nie zfailował grafu.
           VERIFIER ocenił sytuację i zaliczył z ostrzeżeniem. ===
```

---

## S10. Max Subgraph Depth Exceeded

**Context:** Sub-graf zagnieżdża się zbyt głęboko. `max_subgraph_depth=3`. Przy próbie stworzenia grafu z depth=4 → FAIL.

```
S10.1-4  Task T10 → G1 (parent=None, depth=0)
         → PLANNER G1 spawnuje G2 (parent=G1, depth=1)

S10.5   → GraphExecutionCreatedEvent(G2, T10, parent=G1, goal="...", depth=1)
         ├─ Handler: depth=1 ≤ max_subgraph_depth=3 → OK

S10.6-9  [PLANNER G2 spawnuje G3 (parent=G2, depth=2)]
         → GraphExecutionCreatedEvent(G3, T10, parent=G2, goal="...", depth=2)
         ├─ Handler: depth=2 ≤ 3 → OK

S10.10-13 [PLANNER G3 spawnuje G4 (parent=G3, depth=3)]
          → GraphExecutionCreatedEvent(G4, T10, parent=G3, goal="...", depth=3)
          ├─ Handler: depth=3 ≤ 3 → OK (ostatni dozwolony poziom)

S10.14  [PLANNER G4 próbuje spawnąć G5 (parent=G4, depth=4)]
        → GraphExecutionCreatedEvent(G5, T10, parent=G4, goal="...", depth=4)
         ├─ Handler: depth=4 > max_subgraph_depth=3 → FAIL
         └─ emit GraphExecutionFailedEvent(G5, reason="Max subgraph depth exceeded: 4 > 3")

S10.15 → GraphExecutionFailedEvent(G5, reason="Max subgraph depth exceeded: 4 > 3")
         ├─ G5 → FAILED (bez wykonywania)
         ├─ Handler: parent=G4 → czeka na resztę dzieci G4 (tylko G5)
         └─ → SubGraphSettledEvent(parent=G4, child_results=[{G5:FAILED,...}])

S10.16 → SubGraphSettledEvent(parent=G4, child_results[...])
         └─ G4 → PLANNING resume → PLANNER G4 dostaje info że nie mógł zejść głębiej

=== WYNIK: G5 nie powstał — depth check zadziałał. G4 wraca do PLANNERA bez wyników. ===
```

---

## Podsumowanie: Brakujące eventy

Po przeanalizowaniu wszystkich 10 scenariuszy, **jeden event jest niezbędny** a brakuje go w katalogu DOMAINV3 §13:

| # | Brakujący event | Do czego potrzebny |
|---|----------------|-------------------|
| **E1** | **`GraphNodeExecutionTimedOutEvent`** | §10.1 definiuje stan `TIMED_OUT` dla noda. §11.2 definiuje krawędź `TIMEOUT`. Ale **nie ma eventu, który ustawiłby node w stan `TIMED_OUT`**. Obecne eventy noda (§13.3) to tylko: Started (→RUNNING), Completed (→COMPLETED), Failed (→FAILED). Aby krawędź TIMEOUT kiedykolwiek zadziałała, potrzebny jest event przejścia `RUNNING → TIMED_OUT`. |

Pozostałe eventy w katalogu §13 są **wystarczające** do zaorkiestrowania wszystkich 10 scenariuszy.

**Eventy, które rozważałem ale NIE są potrzebne** (bo pokrywa je istniejący mechanizm):

| Rozważany | Dlaczego NIE potrzebny |
|-----------|----------------------|
| Osobny event na "skills have been frozen" | `TaskExecutionCreatedEvent` handler robi to atomowo |
| Event na "graph ready to start" | Scheduler step 4 query'uje PENDING (poling, nie event) |
| Osobny event na `else_target` dla CONDITIONAL | DEFAULT edge obsługuje fallback |
| Event resetujący node dla LOOP | `TransitionLoopedEvent` handler re-startuje PLANNER przez `GraphNodeExecutionStartedEvent` |
| Event na `WorkflowTaskAggregatedEvent` | `TaskExecutionCompletedEvent` handler zapisuje output do `WorkflowStateInput` |

---

## Event trace: pełna lista eventów użytych w symulacjach

| Event | Użyty w scenariuszach |
|-------|---------------------|
| `TaskExecutionCreatedEvent` | S1, S2, S3, S4, S5, S6, S7, S8, S9, S10 |
| `TaskExecutionStartedEvent` | S1, S2, S3, S4, S5, S6, S7, S8, S9, S10 |
| `TaskExecutionCompletedEvent` | S1, S2, S4, S5, S7, S9 |
| `TaskExecutionFailedEvent` | (nie użyty bezpośrednio w symulacjach — zarezerwowany dla nieodwracalnych błędów poza replanem) |
| `TaskExecutionExhaustedEvent` | S3 |
| `GraphExecutionCreatedEvent` | Wszystkie |
| `GraphPlanningStartedEvent` | Wszystkie |
| `GraphSpawnedEvent` | S4, S5, S6, S10 |
| `GraphPlannedEvent` | Wszystkie |
| `SubGraphSettledEvent` | S4, S5, S6, S10 |
| `GraphExecutionCompletedEvent` | S1, S2, S4, S5, S7, S9 |
| `GraphExecutionFailedEvent` | S2, S3, S6, S8, S10 |
| `GraphNodeExecutionStartedEvent` | Wszystkie |
| `GraphNodeExecutionCompletedEvent` | Wszystkie |
| `GraphNodeExecutionFailedEvent` | S9 |
| `TransitionTakenEvent` | Wszystkie |
| `TransitionConditionEvaluatedEvent` | S7 |
| `TransitionLoopedEvent` | S8 |
| `TransitionErrorHandledEvent` | S9 |
| ✳ `GraphNodeExecutionTimedOutEvent` | Zarezerwowany dla timeout noda (nie użyty w symulacjach — brakujący event) |
| ✳ `TransitionTimedOutEvent` | Zarezerwowany dla TIMEOUT krawędzi (nie użyty — czeka na E1 powyżej) |
