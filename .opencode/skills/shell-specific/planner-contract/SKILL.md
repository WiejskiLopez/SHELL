---
name: planner-contract
description: Kontrakt wyjściowy PLANNER node — format, przepływ, implementacja. Używaj przy implementacji/refaktoryzacji planner_result_handler, SubGraphDiscovery, planowania nowych eventów dla plannera.
---

# Planner Contract — jak działa PLANNER node

## 1. Rola Plannera

Planner to `NodeExecution` z `mode=PLANNER`. Jest schedulowany przez Scheduler jak każdy inny node — nie nasłuchuje, nie jest wywoływany ręcznie. Scheduler uruchamia go gdy:
- planner node ma status `ready`
- parent `GraphExecution` ma wszystkie poprzedzające go sub-grafy w statusie `done`

## 2. Format wyjścia (stdout JSON)

Planner po uruchomieniu (subprocess via `PlannerStrategy`) pisze na stdout **jeden** JSON w formacie:

```json
{
  "stage": "Mam pytania dotyczące budżetu. Znalazłem plik budget_2026.xlsx. Task Jira API-123 jest w progress.",
  "spawn": [
    "agent zadający pytania uzupełniające na podstawie stage",
    "agent szukający plików pasujących do budżetu",
    "agent sprawdzający historię taska API-123 w Jira"
  ]
}
```

| Pole | Typ | Obowiązkowy | Opis |
|------|-----|-------------|------|
| `stage` | `string` | tak | Kontekst/informacje zebrane przez plannera podczas analizy. Trafia do `NodeExecution.extra["planner_stage"]`. |
| `spawn` | `string[]` | opcjonalny | Lista zapytań do bazy wektorowej. Każdy string opisuje czego potrzebuje (jaki sub-graf znaleźć). Pusta tablica lub brak → nic nie spawnuje. |

**Zasady:**
- JSON musi być poprawnie sformatowany (jedna linia lub pretty-print)
- `spawn` zachowuje kolejność — scheduler wykonuje childy FIFO z tabeli
- `stage` to czysty tekst, nie JSON wewnątrz JSON
- Brak `plan_id`, `step_id`, `reasoning`, `steps` wrappera

## 3. Przepływ wykonawczy (krok po kroku)

```
Scheduler:
  1. Sprawdza: parent graph ma wszystkie sub-grafy w done? planner node ma status ready?
  2. Tak → uruchamia planner node (PlannerStrategy → subprocess)

Planner node:
  3. Wykonuje się (LLM → analiza → decyzja)
  4. Pisze na stdout: { "stage": "...", "spawn": ["...", "..."] }
  5. Kończy się → NodeExecutionWorker zapisuje ExecutionResult

Worker:
  6. workflow.record_node_execution_result(stdout, stderr, status)
  7. Emituje NodeExecutionCompletedEvent

PlannerResultHandler (subskrybuje NodeExecutionCompletedEvent, sprawdza mode=PLANNER):
  8. Parsuje JSON z result.stdout
  9. stage → NodeExecution.extra["planner_stage"] (zapis w stanie noda)
  10. Dla każdego spawn[i]:
      Emituje SubGraphSpawnRequestedEvent { query: spawn[i], parent_node_id, parent_graph_execution_id, ... }
      → event trafia do tabeli schedulerowej (outbox)
  11. Emituje PlannerSpawnsQueuedEvent { count: len(spawn), parent_node_id }
      → Scheduler ustawia planner node na status waiting

Scheduler (FIFO, odczytuje eventy z tabeli w kolejności):
  12. Odbiera SubGraphSpawnRequestedEvent (pierwszy w kolejce)
  13. SubGraphDiscovery.find_unique(query)
      → Vector DB → embed query → semantic similarity search → top match
      → zwraca GraphDefinitionDto (id, name, purpose, node_definitions)
  14. SubGraphExecutionService.spawn(definition_id, state_input=parent.GraphExecutionState)
      → Materializuje child GraphExecution
      → Emituje eventy do tabeli (GraphExecutionBuiltEvent, etc.)
  15. Wykonuje child GraphExecution (jego node'y)
  16. Child kończy → ChildGraphCompletedEvent
  17. Sprawdza: czy parent planner node ma wszystkie childy w done?
  18. Jeśli nie → czeka / odbiera kolejny SubGraphSpawnRequestedEvent (kolejny FIFO)
      → Powtarza od kroku 13 z następnym spawn[i]
  19. Jeśli tak (wszystkie childy done):
      → Oznacza planner node jako done (status=SUCCESS)
      → Emituje NodeExecutionCompletedEvent dla plannera

NodeExecutionCompletedHandler (Cycle B):
  20. Normalna logika: sprawdza outgoing transitions → advance lub finish workflow
```

## 4. Komponenty do implementacji / refaktoryzacji

### 4.1 Nowy port: `SubGraphDiscovery`

**Path:** `shell/domain/execution/aggregates/node_execution/ports/sub_graph_discovery.py` (lub `shell/domain/execution/ports/`)

```python
"""SubGraphDiscovery Protocol — znajduje GraphDefinition na podstawie opisu."""

from __future__ import annotations

from typing import Protocol

from shell.application.definition.dto.graph_definition import GraphDefinitionDto


class SubGraphDiscovery(Protocol):
    """Znajduje najbardziej pasujący GraphDefinition dla zadanego opisu."""

    async def find_unique(self, query: str) -> GraphDefinitionDto:
        """Zwraca jeden, najlepiej pasujący GraphDefinition.

        Raises:
            GraphDefinitionNotFound: gdy nie znaleziono pasującego grafu.
        """
        ...
```

### 4.2 Nowy adapter: `VectorSubGraphDiscovery`

**Path:** `shell/infrastructure/execution/graph_execution/http/` (lub `shell/infrastructure/execution/discovery/vector_sub_graph_discovery.py` — do stworzenia)

Implementacja:
1. Embeduje `query` do wektora (np. OpenAI Ada, local embedding)
2. Wyszukuje cosine similarity w bazie wektorowej z `GraphDefinition.purpose` / `GraphDefinition.name`
3. Zwraca top match jako `GraphDefinitionDto`

### 4.3 Nowy event: `SubGraphSpawnRequestedEvent`

```python
@dataclass(frozen=True)
class SubGraphSpawnRequestedEvent(DomainEvent):
    query: str                                            # zapytanie do bazy wektorowej
    parent_graph_execution_id: GraphExecutionId           # parent GraphExecution.id
    parent_node_id: NodeExecutionId                       # planner NodeExecution.id
    correlation_id: CorrelationId
```

### 4.4 Nowy event: `PlannerSpawnsQueuedEvent`

```python
@dataclass(frozen=True)
class PlannerSpawnsQueuedEvent(DomainEvent):
    parent_graph_execution_id: GraphExecutionId
    parent_node_id: NodeExecutionId
    spawn_count: int                                       # ile childy zaplanowano
```

### 4.5 Refaktor: `PlannerResultHandler`

**Z:** `shell/application/execution/event_handlers/spawn_sub_graphs_on_planner_completion_handler.py` (do stworzenia/usunięcia)
**Na:** `shell/application/execution/event_handlers/planner_result_handler.py` (do stworzenia)

Kluczowe zmiany:
- Parsuje `{ stage, spawn[] }` zamiast `{ steps: [{ action, sub_graph_definition_id }] }`
- `stage` → `NodeExecution.extra["planner_stage"]`
- `spawn[]` → emituje `SubGraphSpawnRequestedEvent` dla każdego elementu (zamiast bezpośredniego wołania `SubGraphExecutionService.spawn()`)
- Emituje `PlannerSpawnsQueuedEvent` z liczbą spawnów
- Nie wywołuje już `SubGraphExecutionService.spawn()` bezpośrednio

### 4.6 Scheduler — rozszerzenie

Scheduler musi obsługiwać:
- `SubGraphSpawnRequestedEvent` → discovery + spawn + wykonanie childa
- Po każdym childzie: sprawdzić **ile childów parent planner node ma w done** vs **ile zaplanowano** (z `PlannerSpawnsQueuedEvent`)
- Gdy wszystkie → oznaczyć planner node jako done

### 4.7 Do usunięcia

- Stary format `{ steps: [{ action: "spawn_sub_graph", sub_graph_definition_id: "..." }] }` — zastąpiony nowym
- Stary handler `spawn_sub_graphs_on_planner_completion_handler.py` — zastąpiony przez `planner_result_handler.py`

## 5. Diagram przepływu

```
┌─────────────────────────────────────────────────────────────────────┐
│ Scheduler                                                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ 1. Planner node → mode=PLANNER, status=ready                  │   │
│  │    → uruchom subprocess (PlannerStrategy)                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              ↓                                       │
│  stdout: { "stage": "...", "spawn": ["a", "b"] }                    │
│                              ↓                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ 2. NodeExecutionWorker                                   │   │
│  │    → record_node_execution_result()                     │   │
│  │    → NodeExecutionCompletedEvent                         │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              ↓                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ 3. PlannerResultHandler (subskrybuje CompletedEvent)          │   │
│  │    → stage → node.extra["planner_stage"]                     │   │
│  │    → dla spawn[0]: SubGraphSpawnRequestedEvent               │   │
│  │    → dla spawn[1]: SubGraphSpawnRequestedEvent               │   │
│  │    → PlannerSpawnsQueuedEvent { count: 2 }                   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              ↓                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ 4. Scheduler odbiera SubGraphSpawnRequestedEvent (FIFO)       │   │
│  │    → SubGraphDiscovery.find_unique(query)                    │   │
│  │    → Vector DB → GraphDefinitionDto                          │   │
│  │    → SubGraphExecutionService.spawn(definition_id)           │   │
│  │    → child GraphExecution                                    │   │
│  │    → wykonaj child                                           │   │
│  │    → ChildGraphCompletedEvent                                │   │
│  │    → sprawdź: 1/2 childy done → nie wszystkie → czekaj       │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              ↓                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ 5. Scheduler odbiera SubGraphSpawnRequestedEvent #2 (FIFO)    │   │
│  │    → to samo: discovery → spawn → wykonaj                     │   │
│  │    → ChildGraphCompletedEvent                                │   │
│  │    → sprawdź: 2/2 childy done → wszystkie!                    │   │
│  │    → oznacz planner node jako done                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              ↓                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ 6. NodeExecutionCompletedHandler (Cycle B)               │   │
│  │    → outgoing transitions → advance → next node               │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## 6. Reguły i invariants

1. **Planner tylko produkuje JSON** — nie podejmuje decyzji wykonawczych. Decyzje podejmują handlery i scheduler.
2. **Handler nie spawnuje** — handler tylko emituje eventy. Spawning robi scheduler po odczytaniu eventu z tabeli.
3. **Kolejność FIFO** — scheduler odczytuje eventy w kolejności, więc spawny wykonują się w tej samej kolejności co w tablicy.
4. **Sekwencyjność spawnów** — child[1] nie powstanie dopóki child[0] się nie skończy (bo scheduler FIFO, a drugi `SubGraphSpawnRequestedEvent` czeka w kolejce za eventami child[0]).
5. **Stage nie idzie do childów** — stage to notatka plannera, trafia tylko do `NodeExecution.extra["planner_stage"]` w parent planner node. Childy mają dostęp do `GraphExecutionState` parenta.
6. **Scheduler decyduje o zakończeniu** — scheduler śledzi ile childów zaplanowano (`PlannerSpawnsQueuedEvent.count`) vs ile jest done. Gdy wszystkie — oznacza planner node jako done.
