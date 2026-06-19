# SHELL Architecture — Hierarchia

```
Workflow (koordynuje N TaskExecution)
  ├── TaskExecution A (work_dir, własny kontekst)
  │     ├── GraphExecution A1 (główny)
  │     │     ├── GraphNodeExecution: PLANNER
  │     │     ├── GraphNodeExecution: AGENT
  │     │     ├── GraphNodeExecution: TOOL
  │     │     └── child: GraphExecution A1.1 (sub-graf od PLANNER)
  │     │           ├── GraphNodeExecution: TOOL (search)
  │     │           └── GraphNodeExecution: AGENT (summarize)
  │     │                 └── child: GraphExecution A1.1.1 (sub-sub-graf)
  │     │                       └── ...
  │     └── GraphExecution A2 (drugi graf tego samego taska)
  │           └── ...
  │
  └── TaskExecution B (inny task, ten sam Workflow)
        ├── GraphExecution B1 (główny)
        │     ├── GraphNodeExecution: PLANNER
        │     ├── GraphNodeExecution: WORKER
        │     └── child: GraphExecution B1.1
        │           └── ...
        └── GraphExecution B2
              └── ...
```

## Zasady

| Poziom | Opis | Relacja |
|--------|------|---------|
| **Workflow** | Agregat koordynujący wykonywanie tasków | 1 → N TaskExecution (przez TaskExecution.workflow_id) |
| **TaskExecution** | Konkretne zadanie z work_dir, kontekstem | 1 → N GraphExecution, N → 1 Workflow (workflow_id) |
| **GraphExecution** | Instancja grafu (materializacja GraphDefinition) | 1 → N GraphNodeExecution, 0 → N child GraphExecution, N → 1 Workflow (workflow_id) |
| **GraphNodeExecution** | Pojedynczy krok wykonawczy (node) | jeden może być PLANNER |
| **Sub-graf** | GraphExecution będący dzieckiem innego GraphExecution | każde GraphExecution może mieć N dzieci |
| **PLANNER** | Specjalny GraphNodeExecution (mode=planner) | podejmuje decyzje o sub-grafach, może być w dowolnym grafie |

## Kluczowe relacje (DDD — normalizacja)

| Relacja | Gdzie przechowywana | Typ |
|---------|-------------------|-----|
| TaskExecution → Workflow | `TaskExecution.workflow_id` | Klasyczny FK |
| GraphExecution → Workflow | `GraphExecution.workflow_id` | Klasyczny FK |
| GraphExecution → TaskExecution | `GraphExecution.task_execution_id` | Klasyczny FK |
| GraphExecution → parent | `GraphExecution.parent_graph_execution_id` | Self-referencing FK |
| Workflow → nici (odwrotna) | lookup przez `get_by_workflow_id()` | Query |

## Przepływy

### Główny przepływ (bez sub-grafów)
```
Workflow → TaskExecution → GraphExecution → [PLANNER → AGENT → TOOL → ...] → koniec
```

### Z sub-grafami
```
Workflow → TaskExecution → GraphExecution (główny)
  └── PLANNER node:
        1. Analizuje zadanie
        2. Podejmuje decyzję: spawnuj sub-graf
        3. CrownScheduler rejestruje dziecko
        4. GraphExecution (sub-graf) wykonuje się niezależnie
        5. Po zakończeniu → CrownScheduler notify parent
        6. GraphExecution (główny) kontynuuje
```

### Rekurencja sub-grafów
```
GraphExecution A → GraphExecution A.1 → GraphExecution A.1.1 → ...
```
Każdy sub-graf może mieć własnego PLANNER i własne sub-grafy.
