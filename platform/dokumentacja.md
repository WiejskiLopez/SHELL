# Dokumentacja platformy `shell`

> Analiza wygenerowana na podstawie przeglądu kodu. Zawiera opis architektury, przepływ wykonania oraz znalezione błędy logiczne.

---

## 1. Czym jest platforma

Platforma `shell` to lekki silnik agentowy uruchamiany jednowątkowo. Zadania wykonywane są krok po kroku — jeden subproces na raz.  
Wszystkie komponenty komunikują się **przez system plików** (katalogi `.node/input/`, `.node/output/`, `.node/stage/`).

Punkt wejścia to zewnętrzny skrypt (np. `C:\Temp\run-tasker.py`):

```python
from shell.app.app import App

app = App.init_app(mode='tasker', runner_root_dir=__file__)
sys.exit(app.run_app())
```

---

## 2. Tryby pracy (mode)

| Mode     | Opis |
|----------|------|
| `tasker` | Zarządza zadaniem: wczytuje graph YAML, uruchamia node'y jako subprocesy |
| `router` | Odbiera output od agentów i kieruje wiadomości do kolejnych node'ów |
| `agent`  | Wykonuje pracę AI: buduje prompt, wywołuje model CLI, zwraca output |
| `worker` | Jak agent, ale bez LLM — prosta logika, dodatkowe logi |
| `tool`   | Prosta narzędzia bez złożonej logiki (np. wywołanie API) |

---

## 3. Katalog `.node/` — struktura na dysku

Każdy node (agent, router, tasker) ma swój katalog roboczy, np. `C:\temp\workspace\step-2\`:

```
step-2/
  .node/
    input/       ← pliki wejściowe (np. wiadomości do przetworzenia)
    output/      ← pliki wyjściowe (wygenerowane przez agenta)
    stage/
      active/    ← wiadomości aktywnie routowane przez router
      pending/   ← wiadomości czekające na odpowiedź (TTL)
      history/   ← przetworzone wiadomości (archiwum)
      done/      ← wiadomości DONE (koniec zadania)
      ignored/   ← wiadomości przeterminowane (przekroczony max_step)
      dead/      ← wiadomości usunięte z active
    task/        ← kopia <task-name>.yaml i <task-name>.md (odczytywane przez node)
    config/      ← config.yaml node'a
    archive/     ← archiwum po zakończeniu
    logs/        ← logi
```

---

## 4. Format nazwy pliku wiadomości

Wiadomości między node'ami mają ściśle określony format nazwy:

```
n__<from_role>__<to_role>__<msg_type>__<intent>__<thread_id>__<message_id>__<step_number>.md
```

Przykład:
```
1__developer__router__DONE__task_complete__20260503120000123456__20260503120001234567__1.md
```

- `FROM_PLACEHOLDER` (`X`) jest zastępowane przez `source_role` podczas routingu  
- `msg_type == DONE` → router przesyła wiadomość do `stage/done/` i sygnalizuje koniec zadania
- `to_role == router` → wiadomość wraca do historii (odpowiedź na pending)
- Każde przekazanie przez router inkrementuje `step` — po przekroczeniu `max_step` wiadomość trafia do `ignored/`

---

## 5. Przepływ wykonania (mode=tasker)

### 5.1 Inicjalizacja (`App.init_app`)

```
System.validate()
init_app_config(argv, mode, runner_root_dir)
start_trace()
init_app_node(make_dirs)   ← tworzy .node/ dla tasker node'a
lock_.lock()
init_runner(mode='tasker') → init_tasker()
```

### 5.2 `init_tasker()`

```
_init_task_prompts()         ← kopiuje *.prompt.md z source_dir do .node/task/
_validate_task()             ← assert: <task>.yaml i <task>.md istnieją
graph_.init_graph()   ← wczytuje YAML, tworzy GraphNode[] + katalogi node'ów
_init_new_node_statuses()   ← nowe node'y → status INITIALIZED, persystuje do YAML
_seed_graph_node_task()  ← router (non-maker) → READY, task.md → router's task/
```

### 5.3 Pętla główna `_run_iterative_tasker` (do 200 iteracji)

```
1. Szukaj agenta z plikiem w input/:
   → jeśli znaleziony → uruchom agent subproces → continue

2. Szukaj pracy dla routera:
   _has_router_work = jakiś agent ma output/ LUB router.stage/active/ niepuste
                      LUB router.stage/pending/ niepuste
   → jeśli jest praca → uruchom router subproces → jeśli DONE → return DONE → continue

3. "no work" → uruchom router subproces (flush done)
   → jeśli DONE → return DONE
   → break
```

### 5.4 Subproces agenta

```
App.init_app(mode='agent', --node-dir=<agent_dir>, --task-dir=<task_dir>)
init_agent()    ← agent_properties, agent_command, agent_prompt (z placeholders)
run_agent()     ← subprocess.run (LLM CLI) z pętlą retry
```

Agent:
- czyta z `input/` (wiadomość od routera)
- generuje output do `output/` (wiadomość dla routera)
- exit code = Status

### 5.5 Subproces routera

```
App.init_app(mode='router', --node-dir=<router_dir>, --task-dir=<task_dir>)
init_router()   ← init_router_base(task_dir)
run_router()    ← _run_router()
```

Router (non-maker):
```
node_stage.init_stage_dirs()
_expire_pending_ttl()          ← pending z step > max_step → ignored
_pick_agent_output(agent_nodes) ← znajdź output z któregoś agenta
  → jeśli znaleziono:
      _route_incoming()        ← DONE → done/, to_role=router → history, else → active + distribute
  → jeśli nie znaleziono i brak active/:
      _flush_done()            ← kopiuj ostatnią wiadomość z history do tasker output/, exit code=11 (DONE)
```

### 5.6 Mechanizm sygnalizacji DONE

1. Router subprocess: `_flush_done` wywołuje `app.app_trace_.record_info(..., returncode=11)`
2. Router subprocess kończy pracę z `returncode=11`
3. Tasker: `_run_graph_node` zapisuje `returncode=11` do tasker's `app_trace_`
4. Tasker: `app.app_trace_.has_done_` → True → `return Status.DONE`

---

## 6. Graph YAML — przykładowa struktura

```yaml
name: my-task
session_id: null    # generowane przez tasker podczas init

graph:
  - node_name: step-2
    parent_node_dir: C:\temp\workspace
    runner_root_dir: C:\...\agent\cli-agent
    mode: agent
    role: developer
    model: gpt-5-mini
    status: null

  - node_name: step-4
    parent_node_dir: C:\temp\workspace
    runner_root_dir: C:\...\agent\cli-agent
    mode: agent
    role: reviewer
    model: gpt-5-mini
    status: null

  - node_name: step-1
    parent_node_dir: C:\temp\workspace
    runner_root_dir: C:\...\router\default-router
    mode: router
    role: router
    status: null
```

`session_id` jest nadpisywany przez tasker przy każdym `init_tasker()`.  
Statusy node'ów są persystowane do tego samego YAML przez `_persist_node_status`.

---

## 7. RouterBase vs Graph

`RouterBase` posiada własną instancję `Graph` (lazy), inicjalizowaną przez `init_router_base(task_dir)`. Po wywołaniu `_init_router_base` graph jest załadowany z `.node/task/<name>.yaml` i `graph_nodes_` zwraca `list[GraphNode]` (pełne obiekty) — takie same jak w taskerze.

| Kontekst | Jak ładowane | Dostępne? |
|----------|-------------|-----------|
| Tasker subprocess | `graph_.init_graph()` bezpośrednio | ✓ |
| Router subprocess | `router_base_.graph_.init_graph()` via `init_router_base()` | ✓ |

---

## 8. Naprawione błędy (historia)

Wszystkie bugi zidentyfikowane podczas analizy zostały naprawione:

| Bug | Opis | Naprawa |
|-----|------|---------|
| BUG-1 | `_init_router_base.py` był pusty | Teraz wywołuje `graph_.init_graph()` |
| BUG-2 | Router używał `Graph` tasker subprocess zamiast własnego | `_run_router.py` używa `router.router_base_.graph_nodes_` |
| BUG-3 | `task.md` był seedowany do `input/` routera, który go ignorował | Przeniesiono do `task/` (`_seed_graph_node_task`) |
| BUG-4 | `_run_router_maker.py` używał `.node_` zamiast `.graph_node_slot_` | Naprawiono (kod jest dead code — RouterMaker wyłączony) |
| BUG-5 | `_seed_first_agent_input.py` — dead code z błędnym API | Plik usunięty |

---

## 9. Podsumowanie przepływu — aktualny stan

```
Tasker init:
  ✓ Wczytuje graph YAML do GraphNode[]
  ✓ Tworzy katalogi .node/ dla każdego graph node'a
  ✓ Ustawia node'y na INITIALIZED, router na READY
  ✓ _seed_graph_node_task() seeduje task.md do router's task/ (nie input/)

Pętla tasker:
  ✓ Sprawdza agent z input/ (filesystem)
  ✓ Sprawdza router stage (filesystem)
  ✓ Router subprocess otrzymuje graph_nodes z RouterBase (nie pustą listę)

Router subprocess:
  ✓ init_router_base() ładuje graph przez graph_.init_graph()
  ✓ graph_nodes_ zwraca list[GraphNode] (pełne obiekty)
  ✓ _run_router używa router.router_base_.graph_nodes_
  ✓ task.md jest dostępny w task/ (nie w input/)

Agent subprocess:
  ✓ (architektura spójna, nie wymaga zmian)
```

---

## 10. Aktualny stan platformy

Wszystkie znalezione bugi naprawione. Platforma powinna wykonywać pełny cykl:
tasker init → router READY → router subprocess ładuje graph → agenci dostają zadania → router routuje odpowiedzi → DONE.
