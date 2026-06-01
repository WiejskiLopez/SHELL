### .github/copilot-instructions.md
```
﻿# Python coding conventions

## Kontekst projektu

Piszemy w Pythonie prosty system agentowy.

**Platforma:** `C:\Users\palysiewicz\IdeaProjects\MICROSYSTEM\.github\copilot-knowledge\07-automation\platform`

**Tasker** — executor który na podstawie pliku opisu taska i pliku graph generuje strukturę katalogów potrzebną do inicjalizacji wszystkich node'ów taska.
- Przykład opisu taska: `..\tasker\default-tasker\examples\my-task.md`
- Przykład graph: `..\tasker\default-tasker\examples\my-task.yaml`

---

## Zasady ogólne

- Nie dodawaj komentarzy do metod Pythona, a istniejace usuwaj.
- Nie dodawaj komentarz do klas a istniejace usun
- Importy zawsze na górze pliku, nigdy wewnątrz metod.
- Nie używaj skrótów w nazwach zmiennych — pełne nazwy opisowe.

---

## Sloty i properties

- Sloty są zmiennymi prywatnymi z `_` na początku. Dostęp z zewnątrz klasy tylko przez property z sufiksem `_`.
- Nie twórz proxy property bez dodatkowej walidacji — używaj bezpośrednio.
- Nigdy nie odwołuj się do slotu wprost (`_nazwa`) — zawsze przez property (`nazwa_`).

---

## Walidacja slotów

- Slot wymagany: utwórz `_assert_<nazwa>.py` w `internal/` i wywołaj w property. Nigdy `if ... raise` inline w property.
- Slot opcjonalny: zaznacz `Optional` w docstringu klasy, nie waliduj obecności.

---

## Nagłówek klasy

Docstring klasy zawiera sekcję `Slots:` z nazwami pól; opcjonalne oznaczone `Optional`:

```
Slots:
    _app      — parent App
    _dry_run  — Optional; True if --dry-run flag set
```

---

## Inicjalizacja klas

- Konstruktor (`__init__`) tylko zeruje sloty do `None` lub wartości domyślnych — nie zawiera logiki inicjalizacyjnej, nie tworzy obiektów podrzędnych.
- Obiekty podrzędne tworzone są **lazy w property** — property tylko tworzy instancję, nie inicjalizuje jej.
- Logika inicjalizacji idzie do `_init_<nazwa>.py` w `internal/`, wywoływanej przez publiczną metodę `init_<nazwa>()`. Funkcja `_init_*` korzysta z property (nie ze slotu bezpośrednio):

  ```python
  @property
  def foo_(self) -> Foo:
      if self._foo is None:
          self._foo = Foo()
      return self._foo

  def init_foo(self) -> None:
      _init_foo(self)

  # internal/_init_foo.py
  def _init_foo(obj: 'MyClass') -> None:
      obj.foo_.init_foo_bar(obj.bar_)
  ```

- Każda metoda publiczna klasy, która inicjalizuje slot lub sloty, **musi** nazywać się `init_<nazwa>()`. Inne nazwy (np. `build_*`, `create_*`, `setup_*`) są niedozwolone. To samo dotyczy prywatnych funkcji w `internal/` — muszą to być `_init_<nazwa>.py`.
- Nazwy metod publicznych muszą mieć pełną formę: `<akcja>_<na_czym>`, np. `clean_node_input`, `init_node_temp`. Nie używaj skrótów: `clean_input` jest niedozwolone, `clean_node_input` jest poprawne.
- Funkcja wewnętrzna w `internal/` musi mieć nazwę identyczną z metodą publiczną, poprzedzoną `_`, np. metoda `clean_node_temp` → plik `internal/_clean_node_temp.py`, funkcja `_clean_node_temp`.

---

## Klasa Node — dwa konteksty

Klasa `Node` jest używana w dwóch kontekstach. W obu `node_dir` jest przekazywany z zewnątrz.

**AppNode:** `node_dir` z CLI (`--node-dir`) lub fallback `runner_root_dir / ".node"`, inicjalizacja przez `_init_app_node(app)`

**GraphNode:** `node_dir` = `app.app_node_.node_.node_dir_ / node_name`, `node_name` z `graph.yaml`, inicjalizacja przez `_init_graph_node(graph_node, ...)`

---

## Wzorce i konwencje

- Przed napisaniem nowego kodu — przeszukaj istniejący kod i trzymaj się wzorców.
- Jeśli uważasz, że wzorzec jest błędny — zapytaj programistę przed zmianą.

---

## Komentarze i docstringi

Minimalistyczne — tylko to, czego nie da się wywnioskować z kodu.

---

## Operacje na plikach i katalogach

Do wszystkich operacji na plikach i katalogach używamy **wyłącznie** klasy `UtilsPath` (`shell/utils_path/utils_path.py`). Bezpośrednie wywołania metod `Path` (np. `path.mkdir()`, `path.read_text()`) oraz modułów `shutil`, `os` są niedozwolone.

Dostępne metody: `mkdir`, `exists`, `is_file`, `is_dir`, `is_symlink`, `read_text`, `read_text_safe`, `write_text`, `unlink`, `rmtree`, `copy_to`, `move`, `iterdir`, `glob`, `rglob`.

---

## Obsługa błędów i trace

Każda akcja mogąca być źródłem błędu musi być otoczona wywołaniami `record_*` przed i po wykonaniu.


## Workflow Commands

**All commands:** [Workflow Commands Reference](copilot-knowledge/05-engineering/workflows/engineering_workflows_commands.md)

Dot commands (`.done`, `.clean`, `.format`, `.poc`) load and execute workflows automatically.

### `.done` — procedura zamknięcia sesji roboczej

Gdy użytkownik wpisze `.done` na chacie, wykonaj **dokładnie w tej kolejności**:

1. **`git add -A`** — stage wszystkich zmian w katalogu `platform/`
2. **`git commit`** — commit z automatycznym komunikatem opisującym zmiany z bieżącej sesji
3. **`git push`** — wypchnij branch na origin
4. **Utwórz nowy branch** — odczytaj numer z nazwy bieżącego brancha (format `<N>_feature`), zwiększ o 1, utwórz `<N+1>_feature` z `git checkout -b <N+1>_feature` i wypchnij `git push -u origin <N+1>_feature`
5. **Potwierdź** — wyświetl podsumowanie: nazwa commita, stary branch, nowy branch

Wszystkie komendy `git` uruchamiaj w katalogu `C:\Users\palysiewicz\IdeaProjects\schell\platform`.


Narazie w analizie pomijamy modul testowy
```

### agent/cli-agent/config/config.yaml
```
name: cli-agent
mode: agent
role: agent
type: default
# Default configuration for cli-agent.
# Values here are merged with node-level overrides defined in task.yaml.
# Node-level values take priority over these defaults.

log_level: INFO  # Default log level for cli-agent
max_step: 20     # Maximum TTL step; message with step >= max_step is rejected immediately

# LLM model to use (required), default gpt-5-mini
model: gpt-5-mini

# Path to the agent CLI binary. If omitted, the binary must be on PATH.
command: 'C:\Users\palysiewicz\AppData\Roaming\npm\copilot.cmd'

# LLM call timeout in seconds, default 120
timeout: 120

# Number of retries on failure (0 = no retry), default 0
retries: 0

# Delay between retries in seconds, default 1
retry_delay: 1

# If true, do not ask user for input (non-interactive mode), default true
no_ask_user: true

# If true, run in autopilot mode (no confirmation prompts), default true
autopilot: true

```

### agent/cli-agent/entrypoint.py
```
﻿import sys

from shell.app.app import App
def main() -> int:
    app = App.init_app(mode='agent', runner_root_dir=__file__)
    return app.run_app()
if __name__ == "__main__":
    sys.exit(main())
```

### agent/cli-agent/manifest.yaml
```
﻿name: cli-agent
mode: agent
role: agent
type: default
version: 0.1.0
description: "Base CLI Agent."

exit_codes:
  0: SUCCESS
  1: ERROR
  2: TIMEOUT
  3: WARNING
  4: LOCKED
  5: QUESTION
  6: WAITING
  7: SKIP
  8: READY
  9: INITIALIZED
  99: CRITICAL

".<node_name>":  # Node name this name was from --node-dir.name cli param or task-file.yaml graph.node-name tag
  input:         #Input folder for files used by App
  output:        #Output folder for files generated by App
  archive:       #Archive folder for save state after App finish his job
  temp:          #Temporary folder place where App can generate temporary files
  log:           #Folder when loggers App can put his working logs
  config:        #Folder containing config.yaml
  scripts:       #Folder contain scripts using by App, scripts generate working logs
  tools:         #Folder contain tools using by App, tools are extra apps who not generating working logs
  prompt:        #Folder contain system prompt for agent

cli_args:
  --node-dir:  #Path to the  node directory
  --dry-run:   #Optional; validate agent node-dir structure and paths without executing; default empty
  --version:   #Optional; print agent version and exit; default empty
  --help:      #Optional; show manifest and exit; default empty
  --clean:     #Optional; clean output/, logs/ and tmp/, then exit; default empty
  --clean-out: #Optional; clean output/, logs/ and tmp/, then run normally; default empty
  --log-level: #Optional; log level: DEBUG, INFO, WARNING, ERROR, CRITICAL; default INFO
  --timeout:    #Optional; timeout for agent operations in seconds; default was 120 seconds
  --mode:      #Optional; for future multimode support; default is mode from manifest
  --role:      #Optional; for future multirole support; default is role from manifest
  --type:      #Optional; for future multi type support; default is type from manifest
  --no-ask-user: #Optional; working without interaction with human; default empty
  --autopilot:  #Optional; autonomic work; default empty
  --add-dir:    #Optional; extra folders like workspaces what App can use; default empty
  --prompt:    #Optional; prompt as text; default was inside .<node_name>/prompt *.prompt.md
  --prompt-dir: #Optional; prompt as path to files that contain prompt text; default was inside .<node_name>/prompt, support multiple files with *.prompt.md extension
  --work-dir:  #Optional; working directory for agent operations; default c:/temp
  --max-step:  #Optional; maximum TTL step for message routing; default 20
```

### ideas/tasker.md
```
﻿task nic nie robi 


Mamy task A (nadrzedny)

Task sklada sie z: (graph posiadajacego autonomiczne procey na osobnych node)
a)3 sub taski AA,AB,AC (3 osobne node) (taski podrzedne)
b)1 agenta AI (1 node)
c)1 router (1 node) (zapisuje,przesyla, uzupelnia meta)


zarowno agent jak i taski komunkuja sie poprzez interfejsy ktore sa katalogami.
kazdy ma katalog input,output,
dodatkowo kazdy tasker katalog task
struktura podrzedny nadrzedny jest to niekonczace sie drzewo posiadajace pod node 


celem ostatecznym jest by gdy nadrzedny task dostal cos na wejscie input i do katalogu task by z wykorzystaniem subtaskow realizowal zadanie w oparciu o subtaski,
agenta ktory tylko rozdziela zadania decyduje kto nastepny i czy konczymy, na podstawie tego co dostaje na wejscie, 
routera ktory ma za zadanie tylko przesylac fizyczne pliki stanowiace komunikacje miedzy nodami

powiedzmy mamy  task glowny

-napisanie projektu-

i subtaski  analityk co zna temat, programista co umie kodowac i tester co umie testowac, iteracji miedzy nimi moze byc duzo
na koncu to agent decyzyjny podejmuje decyzje na podstawie tego co dostaje na wejscie czy temat konczymy czy tez cos trzeba jednak wykonac, np. testy nie przeszly bo jest
blad w kodzie i trzeba dac informacje developerowi by jeszcze to poprawil


Kazdy komunikt przechodzi przez router w danym tasku w kazdym kroku i kazdy message wygenerowany przez AI lub Sub-taski tam trafia i sie odklada w 
stage (ktory jest takim event-store)(traktowac go mozna jako event source)

W komunikatach poslugujemy sie identyfikatorami
a)session_id, glowny identyfikator zwiazany z sesja 
b)parent_task_id jezeli istnieje task nadrzedny jak to task glowny to mamy NULL 
c)task_id to identyfikator aktualnego taska
d)message_id to identyfikator danego komunikatu
e)counter to kolejna cyfra informujaca o tym ile komunikatow juz dany task_id odlozyl  (append only)
f)status to informacja o tym co soba ten komunikat reprezentuje dla danego taska
REQUESTED
RESPONDED
COMPLETED
FAILED
WAITING
DISPATCHED





pytanie jest takie jak to zorkiestrowac,
inne pytanie czy znasz strony gdzie sa analizy orkiestrowania tego typu pomyslow w oparciu o agentow?





















To co opisujesz to nie jest zwykły „graph”.
To jest:

Hierarchical Multi-Agent Workflow System

albo:

Distributed Agentic Orchestration System

Bardzo podobne koncepcyjnie do:

actor systems,
workflow engines,
blackboard systems,
multi-agent planners,
swarm orchestration,
recursive task decomposition.

I najważniejsze:

NIE buduj tego jako „task wykonuje pracę”

Task powinien być:

tylko kontenerem workflow,
orkiestratorem podzadań,
boundary/contextem.

Realną pracę robią:

subtaski,
agenci,
router.

To bardzo ważna zmiana mentalna.

Co masz realnie

Masz 4 typy node:

Typ	Rola
Task	kontekst workflow
Subtask	wykonawca specjalistyczny
Agent	planner / decider
Router	transport message

To jest bardzo dobra separacja.

Największy problem który musisz rozwiązać

Nie routing.

Nie katalogi.

Tylko:

WORKFLOW STATE

Bo:

task jest bezstanowy,
node są autonomiczne,
workflow jest rozproszony.

Musisz mieć:

shared workflow memory
Kluczowy insight

Nie organizuj tego jako:

folder state

Tylko jako:

MESSAGE GRAPH
Architektura która tu pasuje
1. Envelope

Każda komunikacja musi być:

@dataclass
class Envelope:
    trace_id: str
    workflow_id: str
    parent_workflow_id: str | None

    sender: str
    receiver: str

    message_type: str

    payload: dict
2. Blackboard / Shared Memory

Potrzebujesz czegoś takiego:

workflow/
    job-123/
        memory/
        messages/
        artifacts/
        state.json

Nie jako state taska.

Tylko:

state workflow.
3. Agent nie może tylko „decydować”

Agent musi być:

planner + evaluator

Czyli:

wybiera następny krok,
analizuje wyniki,
może retry,
może rollback,
może terminate.

To de facto:

state machine,
workflow policy engine.
4. Router nie powinien znać logiki

Router:

nie interpretuje,
nie decyduje,
tylko:
przenosi message,
gwarantuje delivery.

Czyli jak Kafka/AMQP.

Jak wygląda flow
Start
TaskA/input/
    specification.md
TaskA agent

analizuje:

"trzeba:
- analiza
- implementacja
- test"
Agent generuje messages
AA <- analyze specification
AB <- implement module
AC <- create tests
Subtaski pracują

Każdy:

czyta input,
produkuje artifacts,
publikuje results.
Agent loop

Agent dostaje:

wyniki,
feedback,
błędy,
test results.

I podejmuje decyzję:

if tests_failed:
    send_to_developer()

elif requirements_missing:
    send_to_analyst()

else:
    finish()
Czyli masz tak naprawdę:
recursive event-driven graph execution
Co bym zrobił architektonicznie
NIE:
task state inferred from directories
TAK:
Workflow Context
@dataclass
class WorkflowContext:
    workflow_id: str
    goal: str

    status: WorkflowStatus

    current_step: str

    artifacts: list[str]

    history: list[Event]
Każdy node:
pobiera context,
robi krok,
emituje event.
Tak naprawdę budujesz coś podobnego do:
System	Podobieństwo
LangGraph	bardzo duże
Temporal	ogromne
Airflow	średnie
CrewAI	duże
AutoGen	bardzo duże
Akka Actors	bardzo duże
Orleans	duże
OpenAI Swarm	duże
Najbliższe Ci koncepcyjnie systemy
LangGraph

Najbardziej.

Bo:

graph orchestration,
agents,
memory,
recursive execution,
loops,
decision nodes.
Microsoft AutoGen

Bardzo podobne do:

analyst,
developer,
tester agents.
CrewAI

Role-based agent orchestration.

Temporal

NIE agentowe, ale:

durable workflows,
orchestration,
retries,
state,
hierarchy.

Bardzo dużo możesz się nauczyć.

Najważniejsza rzecz
NIE buduj workflow z katalogów

Katalogi:

są transportem,
nie stanem.
Stan powinien być jawny

Czyli:

{
  "workflow_id": "...",
  "current_phase": "testing",
  "pending_tasks": [...],
  "completed_tasks": [...],
  "failed_tasks": [...]
}
Inaczej będziesz miał:
race conditions,
deadlocki,
orphan tasks,
niemożliwe recovery,
brak observability.
Bardzo ważny insight

Masz de facto:

distributed recursive state machine

a nie graph.

Gdzie czytać
Agent orchestration
LangGraph docs
AutoGen docs
CrewAI docs
Workflow orchestration
Temporal docs
Cadence Workflow
Actor model
Akka Actors
Microsoft Orleans
Najbardziej production-safe model
workflow
    -> planner agent
        -> generates tasks
            -> workers
                -> emit events
                    -> planner reevaluates

To jest dokładnie wzorzec który opisujesz.




Co realnie zrobiłeś

Router stał się:

event store + transport broker

czyli czymś pomiędzy:

Kafka,
RabbitMQ,
Temporal history,
event bus,
workflow journal.

I to jest bardzo sensowne.

Najważniejszy plus

Nie próbujesz już inferować stanu z tasków.

Tylko:

stan komunikacji,
stan workflow,
siedzi centralnie w routerze.

To ogromny postęp architektoniczny.

Czyli teraz masz
Router

odpowiada za:

delivery,
persistence,
ordering,
journaling,
replay,
traceability.
To jest bardzo ważne

Bo teraz:

task może umrzeć,
node może paść,
agent może restartować się,
a workflow nadal istnieje.

To dokładnie robią production workflow engines.

Twój model zaczyna przypominać
append-only event log

i to jest bardzo dobra architektura.

Teraz najważniejsze
NIE trzymaj „state”

Trzymaj:

EVENT HISTORY

To fundamentalna różnica.

ŹLE
{
  "status": "waiting"
}
DOBRZE
{
  "event": "TASK_ASSIGNED",
  "from": "agent",
  "to": "developer",
  "workflow_id": "123"
}

Potem:

{
  "event": "TASK_COMPLETED"
}

Potem:

{
  "event": "TEST_FAILED"
}

I stan wyliczasz z eventów.

To jest:

Event Sourcing,
CQRS mindset,
workflow journaling.
Katalog stage

To jest dobry pomysł.

Ale:

NIE:
stage = current state
TAK:
stage = immutable event history segment
Czyli np:
router/
    workflows/
        workflow-123/

            stage-0001/
                001_TASK_CREATED.json
                002_ANALYSIS_STARTED.json

            stage-0002/
                003_CODE_GENERATED.json
                004_TEST_STARTED.json
Największa zaleta

Masz:

replay,
audit,
debugging,
observability,
recovery,
deterministic rebuild.

To ogromne.

Co bym dodał koniecznie
1. Monotonic sequence number
{
  "seq": 42
}

bo inaczej:

ordering będzie koszmarem.
2. Correlation id
{
  "workflow_id": "..."
}
3. Parent message id

Do rekonstrukcji graphu:

{
  "parent_message_id": "..."
}
4. Event type

Nigdy nie inferuj eventów z folderów.

5. Immutable messages

Nigdy:

nie edytuj message,
nie nadpisuj.

Tylko append-only.

To bardzo ważne

Bo wtedy możesz:

robić retry,
replay,
compensation,
rollback reasoning.
Tak naprawdę zaczynasz budować

coś pomiędzy:

Temporal + Kafka + LangGraph

tylko filesystem-backed.

Jedna bardzo ważna uwaga
Router nie może być bottleneckiem logicznym

Router:

nie powinien decydować,
nie powinien interpretować AI state,
nie powinien mieć workflow logic.

On ma być:

dumb transport,
durable journal.
Agent powinien czytać historię

I na jej podstawie:

decydować,
planować,
kończyć workflow.
Czyli agent robi:
read event stream
    ->
reason
    ->
emit next commands

To jest idealny pattern dla AI orchestration.

Najbliższy istniejący koncept

To co budujesz jest bardzo podobne do:

Blackboard Architecture

AI systems z lat 80/90.

Wspólna przestrzeń wiedzy + autonomiczne specjalistyczne procesy.

I szczerze:
to jest dużo bardziej naturalne dla agentów niż klasyczne BPMN/workflow engines.

Co bym zrobił dalej
Router:
append-only log,
immutable messages,
ordered delivery,
retry queue,
dead letter queue,
ack mechanism.
Agent:
planner,
evaluator,
termination detector.
Task:
pure worker,
stateless.
Bardzo ważne
Workflow completion

Nie inferuj:

"folder empty"
Tylko explicit event
{
  "event": "WORKFLOW_COMPLETED"
}

To krytyczne dla stabilności systemu.
```

### platform/dokumentacja.md
```
﻿# Dokumentacja platformy `shell`

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
```

### platform/python.good_practics.md
```
Najlepsza praktyka
Low-level
def repository():
    raise DatabaseError(...)

bez logowania.

Mid-level

opcjonalnie:

wrap exception,
dodaj kontekst.
try:
    repository()
except DatabaseError as exc:
    raise ServiceError("User loading failed") from exc
Top-level
try:
    app.run()
except Exception:
    logger.exception("Fatal application error")
```

### platform/shell/__init__.py
```
# lib package
```

### platform/shell/app/__init__.py
```
from shell.app.app.app import App
```

### platform/shell/app/app/__init__.py
```
from shell.app.app.app import App

__all__ = ["App"]
```

### platform/shell/app/app/app.md
```
﻿# Submoduł `app` — klasa `App`

Centralny węzeł DOM dla pojedynczego uruchomienia graph. Przechowuje lazy-referencje do wszystkich modułów.

## Sloty

- `_app_node` — instancja `AppNode`; łącznik z węzłem katalogu.
- `_runner` — instancja `Runner`; zarządza trybem działania aplikacji.
- `_cli` — instancja `Cli`; parametry z wiersza poleceń.
- `_app_config` — instancja `Config`; złożony słownik konfiguracji zbudowany z runtime, CLI i node.
- `_result` — instancja `Result`; stdout/stderr/returncode.
- `_app_trace` — instancja `AppTrace`; dziennik zdarzeń wewnętrznych.
- `_placeholders` — instancja `Placeholders`; dynamiczne mapowanie parametrów konfiguracji.
- `_app_properties` — instancja `AppProperties`; typowane akcesory do `_app_config`.
- `_runtime` — instancja `Runtime`; dane runtime (manifest, runtime_config, runtime_properties).

## Inicjalizacja

Wywołana przez `App.init_app(argv, mode, runner_root_dir)` → `_init_app(cls, ...)`:

1. `app.cli_.init_cli(...)` — parsuje argv, ustawia `runner_root_dir`.
2. `app.runtime_.init_runtime(version_info)` — waliduje system, ładuje `runtime_config` i manifest.
3. `_init_app_modules(app, mode, locker)` — uruchamia trace, inicjalizuje `app_node`, nakłada blokadę, inicjalizuje runner.
4. `_init_app_config(app)` — buduje `app_config_` przez append z `runtime_config`, `cli_config` i `node_config`.

## Właściwości delegujące

- `manifest_` → `runtime_.manifest_`
```

### platform/shell/app/app/app.py
```
"""app.py
App — central runtime state for a shell graph run.

Holds typed references to all module objects and flat configuration values.
Module objects are lazily initialized on first access via properties.
"""

from __future__ import annotations

from typing import Any

from shell.app.app_node.app_node import AppNode
from shell.component.cli.cli.cli import Cli
from shell.component.manifest.manifest import Manifest
from shell.component.config.config.config import Config
from shell.component.placeholders.placeholders import Placeholders
from shell.app.app_trace.app_trace import AppTrace
from shell.app.app_properties.app_properties import AppProperties
from shell.component.result.result import Result
from shell.app.app_runner.app_runner import AppRunner
from shell.component.runtime.runtime.runtime import Runtime
from shell.app.app.internal._init_app import _init_app
from shell.app.app.internal._run_app import _run_app
from shell.app.app.internal._append_app_config import _append_app_config

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_REPR_FIELDS: tuple[str, ...] = ('_result', '_runner')


class App:
    __slots__ = (
        # Private backing slots for module object properties
        '_app_node', '_runner',
        '_cli', '_app_config',
        '_result', '_app_trace',
        '_placeholders',
        '_app_properties',
        '_runtime',
    )

    def __init__(self) -> None:
        self._app_node: AppNode | None = None
        self._runner: AppRunner | None = None
        self._cli: Cli | None = None
        self._app_config: Config | None = None
        self._result: Result | None = None
        self._app_trace: AppTrace | None = None
        self._placeholders: Placeholders | None = None
        self._app_properties: AppProperties | None = None
        self._runtime: Runtime | None = None

    # -----------------------------------------------------------------------
    # Repr
    # -----------------------------------------------------------------------

    def __repr__(self) -> str:
        pairs = ", ".join(
            f"{k}={getattr(self, k)!r}" for k in _REPR_FIELDS
            if getattr(self, k) is not None
        )
        return f"App({pairs})"

    # -----------------------------------------------------------------------
    # Result facade (backward-compat delegating properties)
    # Fields now live in Result but accessed via App for compat.
    # -----------------------------------------------------------------------

    @property
    def result_(self) -> Result:
        """Return the Result singleton for this run."""
        if self._result is None:
            self._result = Result(self)
        return self._result

    @property
    def app_trace_(self) -> AppTrace:
        """Return the AppTrace instance for this run."""
        if self._app_trace is None:
            self._app_trace = AppTrace(self)
        return self._app_trace

    # -----------------------------------------------------------------------
    # Runner facade
    # -----------------------------------------------------------------------

    @property
    def runner_(self) -> AppRunner:
        """Return the cached Runner for this app."""
        if self._runner is None:
            self._runner = AppRunner(self)
        return self._runner

    # AppNode facade
    # -----------------------------------------------------------------------

    @property
    def app_node_(self) -> AppNode:
        """Return the cached AppNode instance for this app."""
        if self._app_node is None:
            self._app_node = AppNode(self)
        return self._app_node


    # AppConfiguration facade
    # -----------------------------------------------------------------------

    @property
    def cli_(self) -> Cli:
        if self._cli is None:
            self._cli = Cli(self)
        return self._cli

    @property
    def manifest_(self) -> Manifest:
        return self.runtime_.manifest_

    @property
    def runtime_(self) -> Runtime:
        if self._runtime is None:
            self._runtime = Runtime(self)
        return self._runtime

    @property
    def app_config_(self) -> Config:
        if self._app_config is None:
            self._app_config = Config(self)
        return self._app_config

    @property
    def placeholders_(self) -> Placeholders:
        if self._placeholders is None:
            self._placeholders = Placeholders(self)
        return self._placeholders

    @property
    def app_properties_(self) -> AppProperties:
        if self._app_properties is None:
            self._app_properties = AppProperties(self)
        return self._app_properties

    # -----------------------------------------------------------------------
    # Phase methods
    # -----------------------------------------------------------------------

    @classmethod
    def init_app(
        cls,
        argv: list[str] | None = None,
        mode: str | None = None,
        runner_root_dir: str | None = None,
        # --- test seams (injectable overrides) ---
        *,
        make_dirs=None,
        version_info: tuple[int, ...] | None = None,
        locker=None,
    ) -> App:
        return _init_app(
            cls,
            argv=argv,
            mode=mode,
            runner_root_dir=runner_root_dir,
            make_dirs=make_dirs,
            version_info=version_info,
            locker=locker,
        )

    def run_app(self) -> int:
        return _run_app(self)

    def append_app_config(self, config_dict: dict, source: str) -> None:
        _append_app_config(self, config_dict, source)

```

### platform/shell/app/app/internal/__init__.py
```
```

### platform/shell/app/app/internal/_append_app_config.py
```
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from shell.app.app.app import App


def _append_app_config(app: App, config_dict: dict, source: Literal['cli', 'sub_node', 'node', 'runtime']) -> None:
    app.app_config_.append_config_dict(config_dict, source)
    app.placeholders_.bind_dict(app.app_config_.config_dict_)
```

### platform/shell/app/app/internal/_archive_app.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.component.result.result import Result

if TYPE_CHECKING:
    from shell.app.app.app import App


def _archive_app(app: App) -> None:
    app._result = Result.from_trace(app.app_trace_, app)
    app.app_node_.node_.node_archive_.save_archive()
    app.result_.save_result()
```

### platform/shell/app/app/internal/_assert_mode_valid.py
```
"""_assert_mode_valid.py
Responsible for one thing: raising ValueError when mode is not in the allowed set.
"""


def _assert_mode_valid(mode: str, modes: frozenset) -> None:
    """Raise ValueError if mode is not in the allowed modes set."""
    if mode not in modes:
        raise ValueError(f"[set_mode] mode must be one of {sorted(modes)}, got: {mode!r}")
```

### platform/shell/app/app/internal/_assert_model_resolved.py
```
def _assert_model_resolved(model: str | None) -> None:
    if not model:
        raise ValueError("[AppConfiguration] model is not set — define it in CLI args or in runner_root_dir/config/config.yaml")
```

### platform/shell/app/app/internal/_finalize_app.py
```
"""_finalize_app.py
Phase — release the lock and clean up after execution.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.app.app.app import App


def _finalize_app(app: 'App', rmtree=None, unlink=None) -> None:
    app.app_node_.release_node(rmtree=rmtree, unlink=unlink)
```

### platform/shell/app/app/internal/_init_app.py
```
"""_init_app.py
Phase 1 — build and return a App from CLI args.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.app.app.internal._init_app_modules import _init_app_modules
from shell.app.app.internal._init_app_config import _init_app_config

if TYPE_CHECKING:
    from shell.app.app.app import App


def _init_app(
    cls,
    argv: list[str] | None = None,
    mode: str | None = None,
    runner_root_dir: str | None = None,
    # --- test seams (injectable overrides) ---
    *,
    make_dirs=None,
    version_info: tuple[int, ...] | None = None,
    locker=None,
) -> App:
    app = cls()
    try:
        app.cli_.init_cli(argv=argv, runner_root_dir=runner_root_dir, mode=mode)
        app.runtime_.init_runtime(version_info=version_info)
        _init_app_modules(app, mode=mode, locker=locker)
        _init_app_config(app)
    except Exception as exc:
        app.app_trace_.record_error_and_raise('app._init_app._init_app', exc)
    return app
```

### platform/shell/app/app/internal/_init_app_config.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.app.app.app import App


def _init_app_config(app: App) -> None:
    app.append_app_config(app.runtime_.runtime_config_.config_dict_, source='runtime')
    app.append_app_config(app.cli_.cli_config_.config_dict_, source='cli')
    app.append_app_config(app.app_node_.node_.node_config_.config_.config_dict_, source='node')
```

### platform/shell/app/app/internal/_init_app_modules.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.app.app.app import App


def _init_app_modules(app: App, mode: str | None, locker) -> None:
    if mode in ('agent', 'tasker', 'router', 'tool', 'worker'):
        app.app_trace_.start_trace()
        app.app_node_.init_app_node()
        app.app_node_.lock_.lock_(locker=locker)
    app.runner_.init_runner(mode=mode)
```

### platform/shell/app/app/internal/_print_app.py
```
"""_print_app.py
Responsible for one thing: printing stdout, stderr and result summary to the output callable.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.app.app.app import App


def _print_app(app: 'App', out: Callable[[str], None]) -> None:
    """Print stdout, stderr and result summary from result_ using the given output callable."""
    result = app.result_

    stdout = result.stdout_ or ''
    if stdout:
        out(stdout)

    stderr = result.stderr_ or ''
    if stderr:
        out(stderr)

    not_save_lines = app.app_trace_.not_save_lines_
    if not_save_lines:
        out(not_save_lines)
```

### platform/shell/app/app/internal/_result_app.py
```
"""_result_app.py
Phase — resolve final status and return the OS exit code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.component.result.result import Result
from shell.app.app.internal._print_app import _print_app

if TYPE_CHECKING:
    from shell.app.app.app import App


def _result_app(app: 'App', out=None) -> int:
    if out is None:
        out = print
    app.app_trace_.record_summary()
    _print_app(app, out)
    return app.result_.returncode_
```

### platform/shell/app/app/internal/_run_app.py
```
"""_run_app.py
Phase — execute the runner, archive, finalize and return the exit code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.app.app.internal._archive_app import _archive_app
from shell.app.app.internal._finalize_app import _finalize_app
from shell.app.app.internal._result_app import _result_app

if TYPE_CHECKING:
    from shell.app.app.app import App

def _run_app(app: 'App') -> int:
    try:
        app.runner_.run_runner()
        app.app_trace_.stop_trace()
        _archive_app(app)
    finally:
        _finalize_app(app)
    return _result_app(app)
```

### platform/shell/app/app/internal/_save_archive.py
```
"""_save_archive.py
Phase — archive the node execution state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.app.app.app import App


def _save_archive(app: 'App', clock=None) -> None:
    app.app_node_.node_.node_archive_.save_archive(clock=clock)
```

### platform/shell/app/app.md
```
# Moduł `app`

Główny moduł aplikacji. Zawiera węzeł korzenny `App` oraz submoduły odpowiedzialne za poszczególne aspekty stanu runtime.

## Submoduły

- `app/` — klasa `App`: centralny węzeł DOM, właściciel wszystkich referencji modułowych.
- `app_node/` — klasa `AppNode`: łącznik między `App` a strukturą katalogową node.
- `app_properties/` — klasa `AppProperties`: typowane akcesory do wartości z `app_config_`.
- `app_trace/` — klasa `AppTrace`: zbiera zdarzenia wykonania (error, warning, info, success).
```

### platform/shell/app/app_node/__init__.py
```
```

### platform/shell/app/app_node/app_node.md
```
# Submoduł `app_node` — klasa `AppNode`

Łącznik między drzewem DOM aplikacji a strukturą katalogową node. Przechowuje uchwyt do głównego `Node` oraz zarządza blokadą na czas wykonania.

## Sloty

- `_app` — referencja do korzenia drzewa (`App`).
- `_node` — Optional; instancja `Node`; lazy.
- `_lock` — Optional; instancja `Locker`; lazy.

## Odpowiedzialność

- Jeden runtime przetwarza dane tylko swojego node — nie wykonuje zadań innych subnodów (może je wyłącznie uruchamiać, ale działają autonomicznie).
- `init_app_node()` — tworzy `Node` z argumentów CLI i struktury katalogu.
- Blokada (`lock_`) zakładana przez `_init_app_modules` na czas wykonania, zdejmowana po zakończeniu.
```

### platform/shell/app/app_node/app_node.py
```
"""app_node.py
AppNode: structured value object for the current node in the context of App.

Analogous to SubNode (which represents a single node in a graph),
AppNode represents the single node that this App instance is executing.

Slots:
    _app  — parent App (DOM back-reference)
    _node — Optional; Node instance, set during init_app_node()
    _lock — Optional; Locker instance, lazy

Validated properties:
    node_dir_        — resolved Path to the node directory
    node_name_       — node directory name (== unique node identifier)
    node_config_     — lazy NodeConfig instance

Methods:
    init_app_node() — create Node from CLI args + node directory structure
"""

from __future__ import annotations

from shell.component.locker.locker import Locker
from shell.structure.node.node.node import Node
from shell.app.app_node.internal._init_app_node import _init_app_node


class AppNode:
    """Structured value object for the current node in the context of App."""

    __slots__ = ("_app", "_node", "_lock")

    def __init__(self, app) -> None:
        self._app = app
        self._node: Node | None = None
        self._lock: Locker | None = None

    # -----------------------------------------------------------------------
    # Node facade
    # -----------------------------------------------------------------------

    @property
    def node_(self) -> Node:
        if self._node is None:
            self._node = Node(self._app)
        return self._node

    # -----------------------------------------------------------------------
    # Lock facade
    # -----------------------------------------------------------------------

    @property
    def lock_(self) -> Locker:
        """Return the cached Locker instance for this node."""
        if self._lock is None:
            self._lock = Locker(self._app)
        return self._lock

    # -----------------------------------------------------------------------
    # Phase method
    # -----------------------------------------------------------------------

    def init_app_node(self) -> None:
        _init_app_node(self._app)

    def release_node(self, rmtree=None, unlink=None) -> None:
        """Release the lock and clean up node directories."""
        self.lock_.unlock()
        if self._app.runner_.mode_ != 'router':
            self._node.clean_node(rmtree=rmtree, unlink=unlink)
```

### platform/shell/app/app_node/internal/__init__.py
```
```

### platform/shell/app/app_node/internal/_init_app_node.py
```
"""_init_app_node.py
Responsible for one thing: initialising the Node instance and creating
the node directory structure for the current App node.
"""

from __future__ import annotations


def _init_app_node(app) -> None:
    cli_properties = app.cli_.cli_properties_
    node_dir = cli_properties.node_dir_ or str((cli_properties.runner_root_dir_ / ".node").resolve())
    app.app_node_.node_.init_node(node_dir=node_dir)
```

### platform/shell/app/app_node/internal/_init_app_node_node.py
```
```

### platform/shell/app/app_properties/__init__.py
```
from shell.app.app_properties.app_properties import AppProperties
```

### platform/shell/app/app_properties/app_properties.md
```
# Submoduł `app_properties` — klasa `AppProperties`

Typowane akcesory do wartości konfiguracji aplikacji — odczytują dane z `App.app_config_`.

## Sloty

- `_app` — referencja do korzenia drzewa (`App`).

## Odpowiedzialność

- `AppProperties` nie posiada własnego magazynu danych — wszystkie wartości czytane przez `self._app.app_config_.config_dict_`.
- Każde property czyta wartość z `config_dict_` i w razie potrzeby ją waliduje.
- Parametr wymagany `name_` — walidacja przez `_assert_app_properties_loaded`.
- Pozostałe parametry opcjonalne — property zwraca `None` gdy brak klucza.

## Właściwości

`name_`, `mode_`, `role_`, `type_`, `model_`, `command_`, `runner_root_dir_`, `script_name_`, `work_dir_`, `timeout_`, `retries_`, `log_level_`, `max_step_`, `no_ask_user_`, `autopilot_`

## Zasada dostępu

Inne moduły odczytują konfigurację przez `app_.app_properties_.<property>_`. `AppProperties` jest źródłem prawdy dla wartości konfiguracyjnych całej aplikacji. Subnode'y mogą posiadać własne konfiguracje, ale gdy ich brakuje — korzystają z `AppProperties`.
```

### platform/shell/app/app_properties/app_properties.py
```
"""app_properties.py
AppProperties — typed accessors for app's config.yaml values.

Slots:
    _app — parent App
"""

from __future__ import annotations

from shell.app.app_properties.internal._assert_app_properties_loaded import _assert_app_properties_loaded


class AppProperties:

    __slots__ = ("_app",)

    def __init__(self, app) -> None:
        self._app = app

    @property
    def name_(self) -> str:
        value = self._app.app_config_.config_dict_.get('name')
        _assert_app_properties_loaded(value)
        return value

    @property
    def mode_(self) -> str | None:
        return self._app.app_config_.config_dict_.get('mode')

    @property
    def role_(self) -> str | None:
        return self._app.app_config_.config_dict_.get('role')

    @property
    def type_(self) -> str | None:
        return self._app.app_config_.config_dict_.get('type')

    @property
    def model_(self) -> str | None:
        return self._app.app_config_.config_dict_.get('model')

    @property
    def command_(self) -> str | None:
        return self._app.app_config_.config_dict_.get('command')

    @property
    def runner_root_dir_(self) -> str | None:
        return self._app.app_config_.config_dict_.get('runner_root_dir')

    @property
    def script_name_(self) -> str | None:
        return self._app.app_config_.config_dict_.get('script_name')

    @property
    def work_dir_(self) -> str | None:
        return self._app.app_config_.config_dict_.get('work_dir')

    @property
    def timeout_(self) -> int | None:
        return self._app.app_config_.config_dict_.get('timeout')

    @property
    def retries_(self) -> int | None:
        return self._app.app_config_.config_dict_.get('retries')

    @property
    def log_level_(self) -> str | None:
        return self._app.app_config_.config_dict_.get('log_level')

    @property
    def max_step_(self) -> int | None:
        return self._app.app_config_.config_dict_.get('max_step')

    @property
    def no_ask_user_(self) -> bool | None:
        return self._app.app_config_.config_dict_.get('no_ask_user')

    @property
    def autopilot_(self) -> bool | None:
        return self._app.app_config_.config_dict_.get('autopilot')
```

### platform/shell/app/app_properties/internal/__init__.py
```
```

### platform/shell/app/app_properties/internal/_assert_app_properties_loaded.py
```
def _assert_app_properties_loaded(name: str | None) -> None:
    if name is None:
        raise ValueError("[AppProperties] not loaded — call init_app_properties() first")
```

### platform/shell/app/app_runner/__init__.py
```
```

### platform/shell/app/app_runner/app_runner.py
```
"""runner.py
Runner — domain methods shared by all runner types.

Owns _app, _agent, _mode and _runner_properties slots.

Domain methods (per spec):
    run_runner(timer)    — dispatch CLI flags to the appropriate domain method
"""

from __future__ import annotations

from shell.module.agent.agent.agent import Agent
from shell.module.router.router.router import Router
from shell.app.app_runner.internal._init_runner import _init_runner
from shell.app.app_runner.internal._run_runner import _run_runner
from shell.app.app_runner.internal._assert_mode_valid import _assert_mode_valid
from shell.module.tasker.tasker import Tasker
from shell.module.tool.tool import Tool
from shell.module.worker.worker.worker import Worker


class AppRunner:
    """Domain methods for a single node run.

    Cached via app.runner_.
    """

    __slots__ = ("_app", "_agent", "_mode", "_tasker", "_router", "_tool", "_worker")

    def __init__(self, app=None) -> None:
        self._app = app
        self._agent: Agent | None = None
        self._mode: str | None = None
        self._tasker: Tasker | None = None
        self._router: Router | None = None
        self._tool: Tool | None = None
        self._worker: Worker | None = None
    # -----------------------------------------------------------------------
    # Slot properties
    # -----------------------------------------------------------------------

    @property
    def agent_(self) -> Agent:
        """Return the cached Agent instance for this runner."""
        if self._agent is None:
            self._agent = Agent(self._app)
        return self._agent

    @property

    def tasker_(self) -> Tasker:
        """Return the cached Tasker instance for this runner."""
        if self._tasker is None:
            self._tasker = Tasker(self._app)
        return self._tasker

    @property
    def router_(self) -> Router:
        """Return the cached Router instance for this runner."""
        if self._router is None:
            self._router = Router(self._app)
        return self._router

    @property
    def tool_(self) -> Tool:
        """Return the cached Tool instance for this runner."""
        if self._tool is None:
            self._tool = Tool(self._app)
        return self._tool

    @property
    def worker_(self) -> Worker:
        """Return the cached Worker instance for this runner."""
        if self._worker is None:
            self._worker = Worker(self._app)
        return self._worker

    def __repr__(self) -> str:
        return f"AppRunner(mode={self._mode!r})"

    @property
    def mode_(self) -> str | None:
        return self._mode

    # -----------------------------------------------------------------------
    # Mode predicates
    # -----------------------------------------------------------------------

    @property
    def is_agent_(self) -> bool:
        return self.mode_ == 'agent'

    @property
    def is_router_(self) -> bool:
        return self.mode_ == 'router'

    @property
    def is_tasker_(self) -> bool:
        return self.mode_ == 'tasker'

    @property
    def is_tool_(self) -> bool:
        return self.mode_ == 'tool'

    @property
    def is_worker_(self) -> bool:
        return self.mode_ == 'worker'

    # -----------------------------------------------------------------------
    # Init
    # -----------------------------------------------------------------------

    def init_runner(self, mode: str | None = None) -> None:
        if mode is not None:
            _assert_mode_valid(mode)
            self._mode = mode
        _init_runner(self)

    # -----------------------------------------------------------------------
    # Dispatch (spec: Runner.run_runner)
    # -----------------------------------------------------------------------

    def run_runner(self, timer=None) -> None:
        """Dispatch CLI flags to the appropriate domain method."""
        _run_runner(self, timer=timer)

```

### platform/shell/app/app_runner/internal/__init__.py
```
```

### platform/shell/app/app_runner/internal/_assert_mode_valid.py
```
from __future__ import annotations


_MODES: frozenset[str] = frozenset({"agent", "tasker", "router", "tool", "worker"})


def _assert_mode_valid(mode: str | None) -> None:
    if mode is None:
        return
    if mode not in _MODES:
        raise ValueError(f"mode must be one of {sorted(_MODES)!r}, got {mode!r}")
```

### platform/shell/app/app_runner/internal/_clean_node.py
```
"""_clean_node.py
Clean node output directories and write result to app.result_.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.app.app_runner.app_runner import AppRunner


def _clean_node(runner: 'AppRunner', timer=None) -> None:
    """Clean node output directories and write result to app.result_."""
    if timer is None:
        timer = time.monotonic
    timer()
    try:
        runner._app.app_node_.node_.clean_node()
        runner._app.app_trace_.record_info('runner._clean_node._clean_node', 'Node output cleaned.')
    except Exception as exc:
        runner._app.app_trace_.record_error_and_raise('runner._clean_node._clean_node', exc)
```

### platform/shell/app/app_runner/internal/_init_runner.py
```
"""_init_runner.py
Initialise the appropriate runner type based on the current mode.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.app.app_runner.app_runner import AppRunner


def _init_runner(runner: 'AppRunner') -> None:
    if runner.is_agent_:
        runner.agent_.init_agent()
    if runner.is_tasker_:
        runner.tasker_.init_tasker()
    if runner.is_router_:
        runner.router_.init_router()
    if runner.is_tool_:
        runner.tool_.init_tool()
    if runner.is_worker_:
        runner.worker_.init_worker()
```

### platform/shell/app/app_runner/internal/_print_help.py
```
"""_print_help.py
Print manifest yaml raw content and write result to app.result_.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.app.app_runner.app_runner import AppRunner


def _print_help(runner: 'AppRunner', timer=None) -> None:
    """Print manifest yaml raw content and write result to app.result_."""
    if timer is None:
        timer = time.monotonic
    timer()
    try:
        output = runner._app.manifest_._manifest_file_body
        runner._app.app_trace_.record_info('runner._print_help._print_help', output)
        runner._app.app_trace_.record_info('runner._print_help._print_help', 'OK')
    except Exception as exc:
        runner._app.app_trace_.record_error_and_raise('runner._print_help._print_help', exc)
```

### platform/shell/app/app_runner/internal/_print_version.py
```
"""_print_version.py
Print agent version and write result to app.result_.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.app.app_runner.app_runner import AppRunner


def _print_version(runner: 'AppRunner', timer=None) -> None:
    if timer is None:
        timer = time.monotonic
    timer()
    try:
        manifest = runner._app.manifest_
        output = f"{manifest._manifest_name_} {manifest._manifest_version_}"
        runner._app.app_trace_.record_info('runner._print_version._print_version', output)
        runner._app.app_trace_.record_info('runner._print_version._print_version', 'OK')
    except Exception as exc:
        runner._app.app_trace_.record_error_and_raise('runner._print_version._print_version', exc)
```

### platform/shell/app/app_runner/internal/_run_runner.py
```
"""_run_runner.py
Dispatch CLI flags to the appropriate runner domain method.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.app.app_runner.internal._clean_node import _clean_node
from shell.app.app_runner.internal._print_help import _print_help
from shell.app.app_runner.internal._print_version import _print_version

if TYPE_CHECKING:
    from shell.app.app_runner.app_runner import AppRunner


def _run_runner(runner: 'AppRunner', timer=None) -> None:
    try:
        if runner._app.cli_.cli_properties_.is_help_:
            _print_help(runner, timer=timer)
        elif runner._app.cli_.cli_properties_.is_version_:
            _print_version(runner, timer=timer)
        elif runner._app.cli_.cli_properties_.is_clean_:
            _clean_node(runner, timer=timer)
        elif runner.is_agent_:
            runner.agent_.run_agent()
        elif runner.is_tasker_:
            runner.tasker_.run_tasker()
        elif runner.is_router_:
            runner.router_.run_router()
        elif runner.is_tool_:
            runner.tool_.run_tool()
        elif runner.is_worker_:
            runner.worker_.run_worker()
        else:
            raise ValueError("Invalid mode: no valid CLI flags found and no valid mode set.")
        runner._app.app_trace_.record_info('runner._run_runner._run_runner', 'successfully executed')
    except Exception as exc:  # noqa: BLE001
        runner._app.app_trace_.record_error('runner._run_runner._run_runner', exc)
```

### platform/shell/app/app_trace/__init__.py
```
```

### platform/shell/app/app_trace/app_trace.md
```
﻿# Submoduł `app_trace` — klasa `AppTrace`

Zbiera zdarzenia wykonania (error, warning, success, info) w trakcie pojedynczego uruchomienia graph.

## Sloty

- `_events` — lista obiektów `Event` zebranych podczas wykonania.
- `_logger` — instancja `Logger`; do wewnętrznego logowania w metodach `record_*`.
- `_start_trace_date_time` — Optional; UTC datetime ustawiony przez `start_trace()`.
- `_stop_trace_date_time` — Optional; UTC datetime ustawiony przez `stop_trace()`.
- `_app_trace_status` — enum `AppTraceStatus`; steruje zachowaniem file-loggera.

## Cykl życia `AppTraceStatus`

- `BEFORE_SAVE` — stan początkowy; zdarzenia zbierane, NIE wysyłane do file-loggera (node_dir jeszcze nie ustawiony).
- `SAVE` — stan normalny; zdarzenia zbierane I wysyłane do file-loggera.
- `AFTER_SAVE` — po podsumowaniu; zdarzenia zbierane tylko do wydruku.

## Odpowiedzialność

- `record_error_and_raise(source, exc)` — rejestruje błąd i re-raise wyjątku.
- `start_trace()` / `stop_trace()` — oznaczają czas trwania sesji.
- `Result.from_trace(app_trace, app)` — buduje wynik końcowy z zebranych zdarzeń.
```

### platform/shell/app/app_trace/app_trace.py
```
"""app_trace.py
AppTrace — collects execution events during a single shell graph run.

Accumulates events (error, warning, success, info) from all phases.
Result is constructed from the trace at the end via Result.from_trace().

Slots:
    _events                           — list of collected Event objects
    _logger                           — Logger instance (for internal logging within record methods)
    _start_trace_date_time            — Optional; UTC datetime set by start_trace() (millisecond precision)
    _stop_trace_date_time             — Optional; UTC datetime set by stop_trace() (millisecond precision)
    _app_trace_status                 — AppTraceStatus enum; controls file-logging behaviour

AppTraceStatus lifecycle:
    BEFORE_SAVE  — initial; events collected, NOT sent to file logger (node_dir not yet set)
    SAVE         — normal; events collected AND sent to file logger
    AFTER_SAVE   — post-summary; events collected for printing only, NOT sent to file logger
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Literal

from shell.app.app_trace.event.event import Event, EventType
from shell.logger.logger import Logger

if TYPE_CHECKING:
    pass

LogLevelCode = Literal['error', 'warning', 'success', 'info']


class AppTraceStatus(Enum):
    BEFORE_SAVE = 'before_save'
    SAVE = 'save'
    AFTER_SAVE = 'after_save'


class AppTrace:
    """Collects execution events for a single graph run."""

    __slots__ = ("_events", "_logger", "_start_trace_date_time", "_stop_trace_date_time", "_app_trace_status")

    def __init__(self, app) -> None:
        self._events: list[Event] = []
        self._logger = Logger(app)
        self._start_trace_date_time: datetime | None = None
        self._stop_trace_date_time: datetime | None = None
        self._app_trace_status: AppTraceStatus = AppTraceStatus.BEFORE_SAVE

    def start_trace(self) -> None:
        _now = datetime.now(timezone.utc)
        self._start_trace_date_time = _now.replace(microsecond=(_now.microsecond // 1000) * 1000)
        self.record_info('app_trace.AppTrace.start_trace', 'session started')

    def stop_trace(self) -> None:
        try:
            _now = datetime.now(timezone.utc)
            self._stop_trace_date_time = _now.replace(microsecond=(_now.microsecond // 1000) * 1000)
            self.record_info('app_trace.AppTrace.stop_trace', 'session stopped')
            self._app_trace_status = AppTraceStatus.AFTER_SAVE
        except Exception as exc:
            self.record_error('app_trace.AppTrace.stop_trace', exc)

    # -----------------------------------------------------------------------
    # Record methods
    # -----------------------------------------------------------------------

    def record_error(self, source: str, exc: Exception, stdout: str = '', stderr: str = '', returncode: int | None = None) -> None:
        """Record an error event."""
        message = str(exc)
        self._try_activate_save_mode()
        if self._app_trace_status != AppTraceStatus.BEFORE_SAVE:
            self._logger.error(f'[{source}] {message}', exc_info=True)
        self._append('error', source, message, stdout, stderr, returncode)

    def record_warning(self, source: str, exc: Exception, stdout: str = '', stderr: str = '', returncode: int | None = None) -> None:
        """Record a warning event."""
        message = str(exc)
        self._try_activate_save_mode()
        if self._app_trace_status != AppTraceStatus.BEFORE_SAVE:
            self._logger.warning(f'[{source}] {message}')
        self._append('warning', source, message, stdout, stderr, returncode)

    def record_error_and_raise(self, source: str, exc: Exception, stdout: str = '', stderr: str = '', returncode: int | None = None) -> None:
        """Record an error event then re-raise the exception."""
        self.record_error(source, exc, stdout, stderr, returncode)
        raise exc

    def record_warning_and_raise(self, source: str, exc: Exception, stdout: str = '', stderr: str = '', returncode: int | None = None) -> None:
        """Record a warning event then re-raise the exception."""
        self.record_warning(source, exc, stdout, stderr, returncode)
        raise exc

    def record_info(self, source: str, message: str, stdout: str = '', stderr: str = '', returncode: int | None = None, event_type: EventType = EventType.SAVE) -> None:
        """Record an informational event."""
        self._try_activate_save_mode()
        if self._app_trace_status != AppTraceStatus.BEFORE_SAVE:
            self._logger.info(f'[{source}] {message}')
        self._append('info', source, message, stdout, stderr, returncode, event_type)

    def record_info_not_save(self, source: str, message: str, stdout: str = '', stderr: str = '', returncode: int | None = None) -> None:
        """Record an informational event that is not written to archive."""
        self._try_activate_save_mode()
        if self._app_trace_status != AppTraceStatus.BEFORE_SAVE:
            self._logger.info(f'[{source}] {message}')
        self._append('info', source, message, stdout, stderr, returncode, EventType.NOT_SAVE)

    def record_summary(self) -> None:
        """Record a NOT_SAVE summary line built from internal trace state."""
        returncode = self.returncode_
        start = self._start_trace_date_time
        stop = self._stop_trace_date_time
        self.record_info_not_save(
            'app_trace.AppTrace.record_summary',
            f"returncode={returncode} start={start.isoformat() if start else None} stop={stop.isoformat() if stop else None}",
            returncode=returncode,
        )

    # -----------------------------------------------------------------------
    # Module facades
    # -----------------------------------------------------------------------

    @property
    def logger_(self) -> Logger:
        return self._logger

    # -----------------------------------------------------------------------
    # Aggregation helpers
    # -----------------------------------------------------------------------

    @property
    def events_(self) -> list[Event]:
        return list(self._events)

    @property
    def has_errors_(self) -> bool:
        return any(e.log_level_code_ == 'error' for e in self.events_)

    @property
    def has_done_(self) -> bool:
        return any(e.returncode_ == 11 for e in self.events_)

    @property
    def has_warnings_(self) -> bool:
        return any(e.log_level_code_ == 'warning' for e in self.events_)

    @property
    def stdout_(self) -> str:
        """Concatenate all success/info messages as stdout."""
        return "\n".join(
            e.formatted_event_line_ for e in self.events_ if e.log_level_code_ in ('success', 'info') and e.event_type_ == EventType.SAVE
        )

    @property
    def stderr_(self) -> str:
        """Concatenate all error/warning messages as stderr."""
        return "\n".join(
            e.formatted_event_line_ for e in self.events_ if e.log_level_code_ in ('error', 'warning') and e.event_type_ == EventType.SAVE
        )

    @property
    def not_save_lines_(self) -> str:
        """Concatenate all NOT_SAVE event lines for end-of-run printing only."""
        return "\n".join(
            e.formatted_event_line_ for e in self.events_ if e.event_type_ == EventType.NOT_SAVE
        )

    @property
    def returncode_(self) -> int:
        """Derive OS exit code from collected events."""
        if self.has_errors_:
            return 1
        if self.has_done_:
            return 11
        if self.has_warnings_:
            return 2
        return 0

    # -----------------------------------------------------------------------
    # Internal
    # -----------------------------------------------------------------------

    def _try_activate_save_mode(self) -> None:
        if self._app_trace_status != AppTraceStatus.BEFORE_SAVE:
            return
        try:
            self._logger._app.app_node_.node_.node_dir_
        except (ValueError, AttributeError):
            return
        self._app_trace_status = AppTraceStatus.SAVE
        buffered = list(self.events_)
        for event in buffered:
            self._flush_event_to_logger(event)

    def _flush_event_to_logger(self, event: Event) -> None:
        source = event._source
        message = event._message
        lc = event._log_level_code
        if lc in ('info', 'success'):
            self._logger.info(f'[{source}] {message}')
        elif lc == 'warning':
            self._logger.warning(f'[{source}] {message}')
        elif lc == 'error':
            self._logger.error(f'[{source}] {message}')

    def _append(
        self,
        log_level_code: LogLevelCode,
        source: str,
        message: str,
        stdout: str = '',
        stderr: str = '',
        returncode: int | None = None,
        event_type: EventType = EventType.SAVE,
    ) -> None:
        event = Event()
        event._log_level_code = log_level_code
        event._event_type = event_type
        event._source = source
        event._message = message
        event._timestamp = datetime.now(timezone.utc)
        event._stdout = stdout
        event._stderr = stderr
        event._returncode = returncode
        self._events.append(event)



```

### platform/shell/app/app_trace/event/__init__.py
```
```

### platform/shell/app/app_trace/event/event.py
```
"""event.py
Event — single execution event collected by AppTrace.

Slots:
    _log_level_code — event type: 'error' | 'warning' | 'success' | 'info'
    _event_type     — EventType.SAVE | EventType.NOT_SAVE; NOT_SAVE events are not written to archive
    _source     — origin label (e.g. 'run_runner', 'init_app')
    _message    — human-readable description
    _timestamp  — UTC datetime of event creation
    _stdout     — Optional; raw stdout
    _stderr     — Optional; raw stderr
    _returncode — Optional; process exit code
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum


class EventType(Enum):
    SAVE = 'save'
    NOT_SAVE = 'not_save'


class Event:
    """Single execution event collected during a graph run."""

    __slots__ = ("_log_level_code", "_event_type", "_source", "_message", "_timestamp", "_stdout", "_stderr", "_returncode")

    def __init__(self) -> None:
        self._log_level_code: str | None = None
        self._event_type: EventType = EventType.SAVE
        self._source: str | None = None
        self._message: str | None = None
        self._timestamp: datetime | None = None
        self._stdout: str | None = None
        self._stderr: str | None = None
        self._returncode: int | None = None

    @property
    def log_level_code_(self) -> str | None:
        return self._log_level_code

    @property
    def event_type_(self) -> EventType:
        return self._event_type

    @property
    def source_(self) -> str | None:
        return self._source

    @property
    def message_(self) -> str | None:
        return self._message

    @property
    def timestamp_iso_(self) -> str | None:
        if self._timestamp is None:
            return None
        return self._timestamp.isoformat(timespec='milliseconds').replace('+00:00', 'Z')

    @property
    def stdout_(self) -> str | None:
        return self._stdout

    @property
    def stderr_(self) -> str | None:
        return self._stderr

    @property
    def returncode_(self) -> int | None:
        return self._returncode

    @property
    def formatted_event_line_(self) -> str:
        errorcode = self._returncode if self._returncode is not None else '-'
        return f"{self.timestamp_iso_} | {self._source} | {errorcode} | {self._message}"
```

### platform/shell/component/__init__.py
```
```

### platform/shell/component/cli/__init__.py
```
from shell.component.cli.cli.cli import Cli

__all__ = ["Cli"]
```

### platform/shell/component/cli/cli/__init__.py
```
from shell.component.cli.cli.cli import Cli

__all__ = ["Cli"]

```

### platform/shell/component/cli/cli/cli.md
```
# Submoduł `cli` — klasa `Cli`

Węzeł DOM reprezentujący sparsowane argumenty CLI.

## Sloty

- `_app` — referencja do korzenia drzewa (`App`).
- `_cli_config` — obiekt klasy `Config` przechowujący parametry CLI; właściciel danych, tworzony lazy w `cli_config_`.
- `_cli_properties` — instancja `CliProperties` (lazy, tworzona w `cli_properties_`).

## Inicjalizacja

Metoda `init_cli(argv, runner_root_dir, mode)` wykonuje dwa kroki:
1. Ustawia `runner_root_dir` w `cli_config_` przez `append_config_value`.
2. `_init_cli` — parsuje `argv` i zapisuje argumenty do `cli_config_` przez `append_config_value`.

Błędy inicjalizacji przechwytywane i przekazywane do `app_trace_`.

```

### platform/shell/component/cli/cli/cli.py
```
from __future__ import annotations

from shell.component.cli.cli.internal._init_cli import _init_cli
from shell.component.cli.cli_properties.cli_properties import CliProperties
from shell.component.config.config.config import Config


class Cli:
    """DOM node for CLI arguments parsed from sys.argv.

    Slots:
        _app            — parent App
        _cli_config     — Config object holding all raw CLI parameter values and defaults
        _cli_properties — CliProperties; typed accessors backed by _cli_config
    """

    __slots__ = (
        "_app",
        "_cli_config",
        "_cli_properties",
    )

    def __init__(self, app=None) -> None:
        self._app = app
        self._cli_config = None
        self._cli_properties = None

    @property
    def cli_config_(self) -> Config:
        if self._cli_config is None:
            self._cli_config = Config()
        return self._cli_config

    @property
    def cli_properties_(self) -> CliProperties:
        if self._cli_properties is None:
            self._cli_properties = CliProperties(self)
        return self._cli_properties

    def init_cli(self, argv=None, runner_root_dir=None, mode: str | None = None) -> None:
        try:
            _init_cli(self, argv=argv, runner_root_dir=runner_root_dir)
        except Exception as exc:
            self._app.app_trace_.record_error_and_raise('cli.Cli.init_cli', exc)
```

### platform/shell/component/cli/cli/internal/__init__.py
```

```

### platform/shell/component/cli/cli/internal/_assert_mode_allowed.py
```
"""_assert_mode_allowed.py
Responsible for one thing: raising ValueError when mode is not one of the allowed CLI modes.
"""


def _assert_mode_allowed(mode: str) -> None:
    """Raise ValueError if mode is not 'agent' or 'tasker'."""
    if mode not in ('agent', 'tasker'):
        raise ValueError(f"[validate_args] mode is required: 'agent' | 'tasker', got: {mode!r}")
```

### platform/shell/component/cli/cli/internal/_assert_model_set.py
```
def _assert_model_set(model: str | None, mode: str | None) -> None:
    if mode == 'agent' and not model:
        raise ValueError("[Cli] --model is required in agent mode")
```

### platform/shell/component/cli/cli/internal/_assert_node_dir_set.py
```
from __future__ import annotations

_MODES_REQUIRING_NODE_DIR = frozenset({'agent', 'tasker', 'router', 'tool', 'worker'})


def _assert_node_dir_set(node_dir: str | None, mode: str | None) -> None:
    if mode in _MODES_REQUIRING_NODE_DIR and node_dir is None:
        raise ValueError(f"[Cli] --node-dir is required in {mode} mode")
```

### platform/shell/component/cli/cli/internal/_assert_runner_root_dir_set.py
```
"""_assert_runner_root_dir_set.py
Responsible for one thing: raising ValueError when runner_root_dir is not set.
"""

from __future__ import annotations


def _assert_runner_root_dir_set(runner_root_dir: str | None) -> None:
    """Raise ValueError if runner_root_dir is None."""
    if runner_root_dir is None:
        raise ValueError("[Cli] runner_root_dir is not set — pass runner_root_dir=__file__ to init_app()")
```

### platform/shell/component/cli/cli/internal/_assert_source_dir_set.py
```
from __future__ import annotations


def _assert_source_dir_set(source_dir: str | None, mode: str | None) -> None:
    if mode == 'tasker' and source_dir is None:
        raise ValueError("[Cli] --source-dir is required in tasker mode")
```

### platform/shell/component/cli/cli/internal/_assert_task_dir_set.py
```
from __future__ import annotations


def _assert_task_dir_set(task_dir: str | None, mode: str | None) -> None:
    if mode == 'router' and task_dir is None:
        raise ValueError("[Cli] --task-dir is required in router mode")
```

### platform/shell/component/cli/cli/internal/_assert_task_name_set.py
```
from __future__ import annotations


def _assert_task_name_set(task_name: str | None, mode: str | None) -> None:
    if mode == 'tasker' and task_name is None:
        raise ValueError("[Cli] --task-name is required in tasker mode")
```

### platform/shell/component/cli/cli/internal/_assert_work_dir_set.py
```
from __future__ import annotations


def _assert_work_dir_set(work_dir: str | None) -> None:
    if work_dir is None:
        raise ValueError("[Cli] --work-dir is required")
```

### platform/shell/component/cli/cli/internal/_init_cli.py
```
from shell.component.cli.cli.internal._parse_args import _parse_args


def _init_cli(cli, argv=None, runner_root_dir=None) -> None:
    config = cli.cli_config_
    config.append_config_value('step_number', '1', 'cli')
    config.append_config_value('allow_all_paths', True, 'cli')
    config.append_config_value('allow_all_tools', True, 'cli')
    config.append_config_value('output_format', 'json', 'cli')
    config.append_config_value('runner_root_dir', runner_root_dir, 'cli')
    args = _parse_args(argv)
    cli.cli_properties_.init_cli_properties(args)
```

### platform/shell/component/cli/cli/internal/_init_cli_placeholders.py
```
def _init_cli_placeholders(cli) -> None:
    cli._app.placeholders_.bind_slots(cli.cli_properties_)
```

### platform/shell/component/cli/cli/internal/_parse_args.py
```
"""parse_args.py
Responsible for one thing: parsing CLI arguments for the agent node.
Returns a parsed ``argparse.Namespace`` object.
"""

import argparse
from typing import Sequence


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments and return a Namespace.

    Supported flags:
        --node-dir <PATH>  Path to the working node.
        --mode <MODE>      Runner mode (agent, tasker, router, worker).
        --role <ROLE>      Node role override.
        --type <TYPE>      Node type override.
        --version          Print the agent version and exit.
        --help             Print the agent help (manifest) and exit.
        --clean            Clean the node output/logs/tmp, then exit.
        --clean_out        Clean the node output/logs/tmp, then run normally.
        --dry-run          Simulate execution without writing output.
        --log-level <LVL>  Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        --no-ask-user      Do not generate questions; finish with SUCCESS or ERROR.
        --autopilot        Run in autonomous loop without user interaction.
        --add-dir <PATH>   Grant access to an additional directory (repeatable).
    """
    parser = argparse.ArgumentParser(
        prog="cli-agent",
        description="Stateless event-driven agent node (v2).",
        add_help=False,
    )
    
    parser.add_argument(
        "--node-dir",
        metavar="PATH",
        default=None,
        dest="node_dir",
        help="Path to the working node.",
    )

    parser.add_argument(
        "--mode",
        metavar="MODE",
        default=None,
        dest="mode",
        help="Runner mode: agent, tasker, router, or worker.",
    )

    parser.add_argument(
        "--role",
        metavar="ROLE",
        default=None,
        dest="role",
        help="Node role override.",
    )

    parser.add_argument(
        "--type",
        metavar="TYPE",
        default=None,
        dest="type",
        help="Node type override.",
    )
    
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print the agent version and exit.",
    )

    parser.add_argument(
        "--help",
        action="store_true",
        dest="help",
        help="Print the agent help (manifest) and exit.",
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean output/, logs/ and tmp/, then exit.",
    )
    
    parser.add_argument(
        "--clean-out",
        action="store_true",
        dest="clean_out",
        help="Clean output/, logs/ and tmp/, then run normally.",
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        dest="dry_run",
        help="Simulate execution without writing output files.",
    )
    
    parser.add_argument(
        "--log-level",
        metavar="LEVEL",
        default=None,
        dest="log_level",
        help="Log level: DEBUG, INFO, WARNING, ERROR, or CRITICAL.",
    )
    
    parser.add_argument(
        "--no-ask-user",
        action="store_true",
        default=False,
        dest="no_ask_user",
        help="Do not generate question files in output/0002_questions/.",
    )
    
    parser.add_argument(
        "--autopilot",
        action="store_true",
        default=True,
        help="Run Copilot in autonomous loop.",
    )

    parser.add_argument(
        "--add-dir",
        metavar="PATH",
        action="append",
        default=[],
        dest="add_dirs",
        help="Grant access to an additional directory (repeatable).",
    )

    parser.add_argument(
        "--prompt",
        metavar="PROMPT",
        default=None,
        dest="prompt",
        help="Prompt override: literal text, path to a file, or path to a directory.",
    )

    parser.add_argument(
        "--prompt-dir",
        metavar="PATH",
        default=None,
        dest="prompt_dir",
        help="Path to directory with *.prompt.md files; overrides default prompt folder.",
    )

    parser.add_argument(
        "--timeout",
        metavar="SECONDS",
        type=int,
        default=None,
        dest="timeout",
        help="Timeout for agent operations in seconds; default 120.",
    )

    # --- tasker-specific ---

    parser.add_argument(
        "--source-dir",
        metavar="PATH",
        default="c:/temp/source",
        dest="source_dir",
        help="Path to source directory containing task files.",
    )

    parser.add_argument(
        "--task-name",
        metavar="NAME",
        default=None,
        dest="task_name",
        help="Name of the task to execute (folder name in task repository).",
    )

    # --- router-specific ---

    parser.add_argument(
        "--model",
        metavar="MODEL",
        default=None,
        dest="model",
        help="LLM model name; required in agent mode.",
    )

    # --- router-specific ---

    parser.add_argument(
        "--task-dir",
        metavar="PATH",
        default=None,
        dest="task_dir",
        help="Path to directory containing task files (.md and .yaml); required in router mode.",
    )

    parser.add_argument(
        "--work-dir",
        metavar="PATH",
        default=None,
        dest="work_dir",
        help="Working directory for agent operations.",
    )

    parser.add_argument(
        "--max-step",
        metavar="N",
        type=int,
        default=None,
        dest="max_step",
        help="Maximum TTL step for message routing; default 20.",
    )

    parser.add_argument(
        "--parent-thread-id",
        metavar="ID",
        default=None,
        dest="parent_thread_id",
        help="Timestamp-based thread id generated by tasker; propagated to all subprocesses.",
    )

    parser.add_argument(
        "--parent-node-dir",
        metavar="PATH",
        default=None,
        dest="parent_node_dir",
        help="Path to the parent tasker node directory; propagated to all subprocesses.",
    )

    return parser.parse_args(argv)
```

### platform/shell/component/cli/cli.md
```
# Moduł `cli`

Odpowiada za parsowanie argumentów wiersza poleceń i udostępnianie ich reszcie aplikacji.

## Odpowiedzialność

- Parsuje `sys.argv` i zapisuje wartości do `CliProperties`.
- Waliduje wymagane parametry — błędy zgłaszane asercjami.
- Jedynym dozwolonym sposobem odczytu parametrów CLI przez inne moduły jest właściwość `cli_properties_`.

## Submoduły

- `cli/` — klasa `Cli`: węzeł DOM przechowujący sparsowane argumenty i aktualizujący placeholdery.
- `cli_properties/` — klasa `CliProperties`: interfejs do parametrów CLI z walidacją i wartościami domyślnymi.
```

### platform/shell/component/cli/cli_properties/__init__.py
```
from shell.component.cli.cli_properties.cli_properties import CliProperties

__all__ = ["CliProperties"]
```

### platform/shell/component/cli/cli_properties/cli_properties.md
```
# Submoduł `cli_properties` — klasa `CliProperties`

Typowane akcesory do parametrów CLI — odczytują dane z obiektu `Config` należącego do `Cli`.

## Sloty

- `_cli` — referencja do rodzica `Cli`; ustawiana przez `Cli.cli_properties_`.

## Odpowiedzialność

- `CliProperties` nie posiada własnego magazynu danych — wszystkie wartości czytane przez `self._cli.cli_config_`.
- Każde property czyta wartość z `config_dict_` i w razie potrzeby ją waliduje.
- Parametry wymagane — walidacja w property przez `_assert_<nazwa>.py` w `internal/`.
- Parametry opcjonalne — property zwraca `None` gdy brak klucza.

## Inicjalizacja

Metoda `init_cli_properties(args)` zapisuje sparsowane argumenty do `Cli.cli_config_` przez `append_config_value`.

## Zasada dostępu

Inne moduły odczytują parametry CLI wyłącznie przez `cli_.cli_properties_.<property>_`. Bezpośredni dostęp do `_cli` spoza modułu jest niedozwolony.
```

### platform/shell/component/cli/cli_properties/cli_properties.py
```
from __future__ import annotations

from shell.utils.path.path import Path, PathType
from datetime import datetime

from shell.component.cli.cli.internal._assert_runner_root_dir_set import _assert_runner_root_dir_set
from shell.component.cli.cli_properties.internal._init_cli_properties import _init_cli_properties


class CliProperties:
    """Typed accessors for CLI parameter values; backed by Cli._cli_config.

    Slots:
        _cli — reference to the owning Cli; set by Cli.cli_properties_
    """

    __slots__ = ("_cli",)

    def __init__(self, cli=None) -> None:
        self._cli = cli

    @property
    def is_version_(self) -> bool:
        return self._cli.cli_config_.config_dict_.get('version') is True

    @property
    def is_help_(self) -> bool:
        return self._cli.cli_config_.config_dict_.get('help') is True

    @property
    def is_clean_(self) -> bool:
        return self._cli.cli_config_.config_dict_.get('clean') is True

    @property
    def is_clean_out_(self) -> bool:
        return self._cli.cli_config_.config_dict_.get('clean_out') is True

    @property
    def is_dry_run_(self) -> bool:
        return self._cli.cli_config_.config_dict_.get('dry_run') is True

    @property
    def is_no_ask_user_(self) -> bool:
        return self._cli.cli_config_.config_dict_.get('no_ask_user') is True

    @property
    def is_autopilot_(self) -> bool:
        return self._cli.cli_config_.config_dict_.get('autopilot') is True

    @property
    def is_allow_all_paths_(self) -> bool:
        return self._cli.cli_config_.config_dict_.get('allow_all_paths') is True

    @property
    def is_allow_all_tools_(self) -> bool:
        return self._cli.cli_config_.config_dict_.get('allow_all_tools') is True

    @property
    def output_format_(self) -> str:
        return self._cli.cli_config_.config_dict_.get('output_format', 'json')

    @property
    def prompt_(self) -> str | None:
        return self._cli.cli_config_.config_dict_.get('prompt')

    @property
    def node_dir_(self) -> str | None:
        return self._cli.cli_config_.config_dict_.get('node_dir')

    @property
    def mode_(self) -> str | None:
        return self._cli.cli_config_.config_dict_.get('mode')

    @property
    def role_(self) -> str | None:
        return self._cli.cli_config_.config_dict_.get('role')

    @property
    def log_level_(self) -> str | None:
        return self._cli.cli_config_.config_dict_.get('log_level')

    @property
    def runner_root_dir_(self) -> PathType:
        value = self._cli.cli_config_.config_dict_.get('runner_root_dir')
        _assert_runner_root_dir_set(value)
        return Path.new(value).parent.resolve()

    @property
    def source_dir_(self) -> PathType | None:
        value = self._cli.cli_config_.config_dict_.get('source_dir')
        if value is None:
            return None
        return Path.new(value).resolve()

    @property
    def task_name_(self) -> str | None:
        return self._cli.cli_config_.config_dict_.get('task_name')

    @property
    def task_dir_(self) -> PathType | None:
        value = self._cli.cli_config_.config_dict_.get('task_dir')
        if value is None:
            return None
        return Path.new(value).resolve()

    @property
    def model_(self) -> str | None:
        return self._cli.cli_config_.config_dict_.get('model')

    @property
    def work_dir_(self) -> str | None:
        return self._cli.cli_config_.config_dict_.get('work_dir')

    @property
    def max_step_(self) -> int:
        value = self._cli.cli_config_.config_dict_.get('max_step')
        if value is None:
            return 20
        return value

    @property
    def step_number_(self) -> str:
        return self._cli.cli_config_.config_dict_.get('step_number', '1')

    @property
    def parent_thread_id_(self) -> str | None:
        return self._cli.cli_config_.config_dict_.get('parent_thread_id')

    @property
    def parent_node_dir_(self) -> PathType | None:
        value = self._cli.cli_config_.config_dict_.get('parent_node_dir')
        if value is None:
            return None
        return Path.new(value).resolve()

    @property
    def message_id_(self) -> str:
        return datetime.now().strftime('%Y%m%d%H%M%S%f')

    @property
    def thread_id_(self) -> str:
        if 'thread_id' not in self._cli.cli_config_.config_dict_:
            self._cli.cli_config_.append_config_value('thread_id', datetime.now().strftime('%Y%m%d%H%M%S%f'), 'cli')
        return self._cli.cli_config_.config_dict_['thread_id']

    @property
    def add_dirs_(self) -> list[str]:
        return self._cli.cli_config_.config_dict_.get('add_dirs') or []

    def init_cli_properties(self, args) -> None:
        _init_cli_properties(self, args)
```

### platform/shell/component/cli/cli_properties/internal/__init__.py
```
```

### platform/shell/component/cli/cli_properties/internal/_init_cli_properties.py
```
from shell.component.cli.cli.internal._assert_node_dir_set import _assert_node_dir_set
from shell.component.cli.cli.internal._assert_source_dir_set import _assert_source_dir_set
from shell.component.cli.cli.internal._assert_task_name_set import _assert_task_name_set
from shell.component.cli.cli.internal._assert_task_dir_set import _assert_task_dir_set
from shell.component.cli.cli.internal._assert_model_set import _assert_model_set
from shell.component.cli.cli.internal._assert_work_dir_set import _assert_work_dir_set


def _init_cli_properties(cli_properties, args) -> None:
    config = cli_properties._cli.cli_config_
    if args.add_dirs:
        config.append_config_value('add_dirs', args.add_dirs, 'cli')
    if args.node_dir is not None:
        config.append_config_value('node_dir', args.node_dir, 'cli')
    if args.mode is not None:
        config.append_config_value('mode', args.mode, 'cli')
    if args.role is not None:
        config.append_config_value('role', args.role, 'cli')
    if args.type is not None:
        config.append_config_value('type', args.type, 'cli')
    if args.version:
        config.append_config_value('version', True, 'cli')
    if args.help:
        config.append_config_value('help', True, 'cli')
    if args.clean:
        config.append_config_value('clean', True, 'cli')
    if args.clean_out:
        config.append_config_value('clean_out', True, 'cli')
    if args.dry_run:
        config.append_config_value('dry_run', True, 'cli')
    if args.log_level is not None:
        config.append_config_value('log_level', args.log_level, 'cli')
    if args.no_ask_user:
        config.append_config_value('no_ask_user', True, 'cli')
    if args.autopilot:
        config.append_config_value('autopilot', True, 'cli')
    if args.prompt is not None:
        config.append_config_value('prompt', args.prompt, 'cli')
    if args.prompt_dir is not None:
        config.append_config_value('prompt_dir', args.prompt_dir, 'cli')
    if args.timeout is not None:
        config.append_config_value('timeout', args.timeout, 'cli')
    if args.source_dir is not None:
        config.append_config_value('source_dir', args.source_dir, 'cli')
    if args.task_name is not None:
        config.append_config_value('task_name', args.task_name, 'cli')
    if args.task_dir is not None:
        config.append_config_value('task_dir', args.task_dir, 'cli')
    if args.model is not None:
        config.append_config_value('model', args.model, 'cli')
    config.append_config_value('work_dir', args.work_dir, 'cli')
    if args.max_step is not None:
        config.append_config_value('max_step', args.max_step, 'cli')
    if args.parent_thread_id is not None:
        config.append_config_value('parent_thread_id', args.parent_thread_id, 'cli')
    if args.parent_node_dir is not None:
        config.append_config_value('parent_node_dir', args.parent_node_dir, 'cli')
    d = config.config_dict_
    _assert_node_dir_set(d.get('node_dir'), d.get('mode'))
    _assert_source_dir_set(d.get('source_dir'), d.get('mode'))
    _assert_task_name_set(d.get('task_name'), d.get('mode'))
    _assert_task_dir_set(d.get('task_dir'), d.get('mode'))
    _assert_model_set(d.get('model'), d.get('mode'))
    _assert_work_dir_set(d.get('work_dir'))
```

### platform/shell/component/command/__init__.py
```
```

### platform/shell/component/command/command/internal/_assert_add_dir_exists.py
```
from shell.utils.path.path import Path, PathType


def _assert_add_dir_exists(add_dir: PathType) -> None:
    if not Path.is_dir(add_dir):
        raise FileNotFoundError(f"Add directory does not exist: {add_dir}")
```

### platform/shell/component/command/command/internal/_assert_copilot_cmd_found.py
```
def _assert_copilot_cmd_found(command) -> None:
    if not command:
        raise FileNotFoundError(
            "Agent CLI not found. Set command in app/app.yaml "
            "or ensure the binary is on PATH."
        )
```

### platform/shell/component/command/command/internal/_assert_log_dir_exists.py
```
from shell.utils.path.path import Path, PathType


def _assert_log_dir_exists(log_dir: PathType) -> None:
    if not Path.is_dir(log_dir):
        raise FileNotFoundError(f"Log directory does not exist: {log_dir}")
```

### platform/shell/component/command/command/internal/_assert_model_set.py
```
def _assert_model_set(model: str) -> None:
    if not model:
        raise ValueError("[Command] Required field missing: 'model'")
```

### platform/shell/component/command/command/internal/_assert_output_dir_exists.py
```
from shell.utils.path.path import Path, PathType


def _assert_output_dir_exists(output_dir: PathType) -> None:
    if not Path.is_dir(output_dir):
        raise FileNotFoundError(f"Output directory does not exist: {output_dir}")
```

### platform/shell/component/command/command/internal/_assert_source_dir_set.py
```
def _assert_source_dir_set(source_dir) -> None:
    if not source_dir:
        raise RuntimeError("[Command] source_dir is not set — pass --source-dir to the CLI")
```

### platform/shell/component/command/command/internal/_assert_task_dir_set.py
```
def _assert_task_dir_set(task_dir) -> None:
    if not task_dir:
        raise RuntimeError("[Command] task_dir is not set — pass --task-dir to the CLI")
```

### platform/shell/component/command/command/internal/_assert_task_name_set.py
```
def _assert_task_name_set(task_name) -> None:
    if not task_name:
        raise RuntimeError("[Command] task_name is not set — pass --task-name to the CLI")
```

### platform/shell/component/command/command/internal/_assert_work_dir_set.py
```
def _assert_work_dir_set(work_dir) -> None:
    if not work_dir:
        raise RuntimeError("[Command] work_dir is not set — pass --work-dir to the CLI")
```

### platform/shell/component/command/command/internal/_init_command_agent.py
```
from __future__ import annotations

import os
import shutil

from shell.component.command.command.internal._assert_copilot_cmd_found import _assert_copilot_cmd_found
from shell.component.command.command.internal._assert_model_set import _assert_model_set
from shell.component.command.command.internal._assert_output_dir_exists import _assert_output_dir_exists
from shell.component.command.command.internal._assert_log_dir_exists import _assert_log_dir_exists
from shell.component.command.command.internal._assert_add_dir_exists import _assert_add_dir_exists
from shell.constants.constants import DOT_NODE, DIR_OUTPUT


def _init_command_agent(command, app, which=None, os_name=None) -> None:
    which = which or shutil.which
    os_name = os_name or os.name

    binary = which("copilot")
    _assert_copilot_cmd_found(binary)

    if os_name == "nt" and str(binary).lower().endswith((".cmd", ".bat")):
        command.extend_command_args(["cmd", "/c", binary])
    else:
        command.add_command_arg(binary)

    model = (app.runner_.agent_.agent_properties_.model_ or "").strip()
    _assert_model_set(model)
    command.extend_command_args(["--model", model])

    if app.cli_.cli_properties_.is_allow_all_paths_:
        command.add_command_arg("--allow-all-paths")

    if app.cli_.cli_properties_.is_allow_all_tools_:
        command.add_command_arg("--allow-all-tools")

    command.extend_command_args(["--output-format", app.cli_.cli_properties_.output_format_])

    if app.cli_.cli_properties_.is_no_ask_user_:
        command.add_command_arg("--no-ask-user")

    if app.cli_.cli_properties_.is_autopilot_:
        command.add_command_arg("--autopilot")

    output_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_OUTPUT
    _assert_output_dir_exists(output_dir)
    command.extend_command_args(["--add-dir", str(output_dir)])
    app.app_trace_.record_info('command._init_command_agent', f'--add-dir {output_dir}')

    logs_dir = app.app_node_.node_.node_logs_.logs_dir_
    _assert_log_dir_exists(logs_dir)

    for add_dir in app.cli_.cli_properties_.add_dirs_:
        _assert_add_dir_exists(add_dir)
        command.extend_command_args(["--add-dir", str(add_dir)])
        app.app_trace_.record_info('command._init_command_agent', f'--add-dir {add_dir}')

    node_dir = app.app_node_.node_.node_dir_
    _assert_add_dir_exists(node_dir)
    command.extend_command_args(["--add-dir", str(node_dir)])
    app.app_trace_.record_info('command._init_command_agent', f'--add-dir {node_dir}')

    command.extend_command_args(["--log-dir", str(logs_dir)])
    app.app_trace_.record_info('command._init_command_agent', f'--log-dir {logs_dir}')
```

### platform/shell/component/command/command/internal/_init_command_sub_node.py
```
from __future__ import annotations

import sys

from shell.utils.path.path import Path
from shell.structure.sub_node.sub_node.internal._assert_entrypoint_exists import _assert_entrypoint_exists
from shell.component.command.command.internal._assert_source_dir_set import _assert_source_dir_set
from shell.component.command.command.internal._assert_task_dir_set import _assert_task_dir_set
from shell.component.command.command.internal._assert_task_name_set import _assert_task_name_set
from shell.component.command.command.internal._assert_work_dir_set import _assert_work_dir_set
from shell.component.command.command.internal._assert_model_set import _assert_model_set


def _init_command_sub_node(command, sub_node_properties, task_dir, app, python_exe=None) -> None:
    if python_exe is None:
        python_exe = sys.executable

    sub_node_name = sub_node_properties.sub_node_name_
    parent_node_dir = sub_node_properties.parent_node_dir_
    runner_root_dir = sub_node_properties.sub_node_runner_root_dir_
    mode = sub_node_properties.mode_
    model = sub_node_properties.model_
    cli = app.cli_
    task_name = sub_node_properties.task_name_ or cli.task_name_
    source_dir = sub_node_properties.source_dir_ or cli.source_dir_
    work_dir = sub_node_properties.work_dir_ or cli.work_dir_
    thread_id = cli.thread_id_

    _assert_source_dir_set(source_dir)
    _assert_work_dir_set(work_dir)
    _assert_task_name_set(task_name)
    _assert_task_dir_set(task_dir)

    node_dir = Path.new(parent_node_dir) / sub_node_name
    entrypoint_path = Path.new(runner_root_dir).resolve() / 'entrypoint.py'
    _assert_entrypoint_exists(entrypoint_path)

    command.extend_command_args([python_exe, str(entrypoint_path)])
    command.extend_command_args(['--node-dir', str(node_dir)])
    command.extend_command_args(['--source-dir', str(source_dir)])
    command.extend_command_args(['--work-dir', str(work_dir)])
    command.extend_command_args(['--task-name', task_name])
    command.extend_command_args(['--task-dir', str(task_dir)])

    if parent_node_dir is not None:
        command.extend_command_args(['--parent-node-dir', str(parent_node_dir)])
        app.app_trace_.record_info('command._init_command_sub_node', f'parent_node_dir set: {parent_node_dir}')
    else:
        app.app_trace_.record_info('command._init_command_sub_node', 'parent_node_dir not set')

    if thread_id is not None:
        command.extend_command_args(['--parent-thread-id', thread_id])

    if mode == 'agent':
        _assert_model_set(model)
        command.extend_command_args(['--model', model])

    role = sub_node_properties.role_
    if role is not None:
        command.extend_command_args(['--role', role])

    timeout = sub_node_properties.timeout_
    if timeout is not None:
        command.extend_command_args(['--timeout', str(timeout)])
```

### platform/shell/component/command/command.py
```
"""command.py
Command — value object wrapping a CLI command as a list of string arguments.

Slots:
    _command — list[str]; the assembled CLI arguments
"""

from __future__ import annotations


class Command:
    """Value object wrapping a CLI command argument list."""

    __slots__ = ("_command",)

    def __init__(self, command: list[str]) -> None:
        self._command = command

    @property
    def command_(self) -> list[str]:
        return self._command

    def add_command_arg(self, arg: str) -> None:
        self._command.append(arg)

    def extend_command_args(self, args: list[str]) -> None:
        self._command.extend(args)
```

### platform/shell/component/config/__init__.py
```
```

### platform/shell/component/config/config/__init__.py
```

```

### platform/shell/component/config/config/config.py
```
"""config.py
Config: holder for the default config.yaml loaded from runner_root_dir.

Slots:
    _app         — parent App (DOM back-reference)
    _config_path — path to the config.yaml file on disk
    _config_dict — parsed YAML dict
"""

from __future__ import annotations

from shell.utils.path.path import Path, PathType
from typing import Literal

from shell.component.config.config.internal._append_config_dict import _append_config_dict
from shell.component.config.config.internal._append_config_from_path import _append_config_from_path
from shell.component.config.config.internal._append_config_value import _append_config_value
from shell.component.config.config.internal._assert_config_path_set import _assert_config_path_set
from shell.component.config.config.internal._assert_model_set import _assert_model_set
from shell.component.config.config.internal._init_config import _init_config


class Config:
    """Raw default config.yaml for a single node run.

    Constructed as Config(app) — held as app.config_,
    loaded once during init_app_configuration().
    """

    __slots__ = ("_app", "_config_path", "_config_dict")

    def __init__(
        self,
        app=None,
        config_path: PathType | str | None = None,
    ) -> None:
        self._app = app
        self._config_path: PathType | None = Path.new(config_path) if config_path else None
        self._config_dict: dict | None = None

    @property
    def config_dict_(self) -> dict:
        if not self._config_dict:
            return {}
        return {k: v['value'] for k, v in self._config_dict.items()}

    @property
    def config_path_(self) -> PathType:
        _assert_config_path_set(self._config_path)
        return Path.new(self._config_path).resolve()

    def init_config(self, config_path: PathType | str, source: str) -> None:
        _init_config(self, config_path, source)

    def append_config_value(self, key: str, value, source: Literal['cli', 'sub_node', 'node', 'runtime']) -> None:
        _append_config_value(self, key, value, source)

    def append_config_dict(self, config_dict: dict, source: Literal['cli', 'sub_node', 'node', 'runtime']) -> None:
        _append_config_dict(self, config_dict, source)

    def append_config_from_path(self, config_path: PathType | str, source: Literal['cli', 'sub_node', 'node', 'runtime']) -> None:
        _append_config_from_path(self, config_path, source)
```

### platform/shell/component/config/config/internal/__init__.py
```
```

### platform/shell/component/config/config/internal/_append_config_dict.py
```
from __future__ import annotations

from shell.component.config.config.internal._append_config_value import _append_config_value


def _append_config_dict(config: object, config_dict: dict, source: str) -> None:
    for key, value in config_dict.items():
        if value is not None:
            _append_config_value(config, key, value, source)
```

### platform/shell/component/config/config/internal/_append_config_from_path.py
```
from __future__ import annotations

import yaml

from shell.component.config.config.internal._append_config_dict import _append_config_dict
from shell.utils.path.path import Path, PathType


def _append_config_from_path(config: object, config_path: PathType | str, source: str) -> None:
    config._config_path = Path.new(config_path)
    if not Path.is_file(config._config_path):
        return
    raw = yaml.safe_load(Path.read_text(config._config_path)) or {}
    _append_config_dict(config, raw, source)
```

### platform/shell/component/config/config/internal/_append_config_value.py
```
from __future__ import annotations

import yaml

from typing import Literal

from shell.utils.path.path import Path


def _append_config_value(config: 'Config', key: str, value, source: Literal['cli', 'sub_node', 'node', 'runtime']) -> None:
    if config._config_dict is None:
        config._config_dict = {}
    existing = config._config_dict.get(key)
    if existing is None:
        config._config_dict[key] = {'value': value, 'source': source}
    elif source == 'cli':
        config._config_dict[key] = {'value': value, 'source': source}
    elif source == 'sub_node' and existing['source'] in ('runtime', 'node'):
        config._config_dict[key] = {'value': value, 'source': source}
    elif source == 'node' and existing['source'] == 'runtime':
        config._config_dict[key] = {'value': value, 'source': source}
    if config._config_path is not None:
        flat = {k: v['value'] for k, v in config._config_dict.items()}
        Path.write_text(config._config_path, yaml.dump(flat, default_flow_style=False, allow_unicode=True))
```

### platform/shell/component/config/config/internal/_assert_config_body_loaded.py
```
def _assert_config_body_loaded(body: str) -> None:
    if not body.strip():
        raise ValueError("[Config] config_file_body is empty — call init_config() first")
```

### platform/shell/component/config/config/internal/_assert_config_path_set.py
```
def _assert_config_path_set(path) -> None:
    if not path:
        raise ValueError("[Config] config_path is not set")
```

### platform/shell/component/config/config/internal/_assert_model_set.py
```
def _assert_model_set(config_dict: dict | None) -> None:
    if not config_dict or 'model' not in config_dict:
        raise ValueError("[Config] 'model' key missing in config.yaml")
```

### platform/shell/component/config/config/internal/_init_config.py
```
from __future__ import annotations

import yaml

from shell.utils.path.path import Path, PathType


def _init_config(config: 'Config', config_path: PathType | str, source: str) -> None:
    config_path = Path.new(config_path)
    try:
        config._config_path = config_path
        raw = yaml.safe_load(Path.read_text(config_path)) or {}
        config._config_dict = {k: {'value': v, 'source': source} for k, v in raw.items()}
    except Exception as exc:
        config._app.app_trace_.record_error_and_raise('config.Config.init_config', exc)
```

### platform/shell/component/config/internal/__init__.py
```
```

### platform/shell/component/locker/__init__.py
```
# lib/lock package
```

### platform/shell/component/locker/internal/__init__.py
```
```

### platform/shell/component/locker/internal/_acquire_locker.py
```
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from shell.utils.path.path import PathType
from shell.component.locker.internal._acquire_node_dir_lock import acquire_node_dir_lock
from shell.component.locker.internal._lock_error import LockError
from shell.component.result.result import Result

if TYPE_CHECKING:
    from shell.component.locker.locker import Locker


def _acquire_locker(locker: 'Locker', acquirer: Callable[[PathType], PathType] | None = None) -> None:
    if acquirer is None:
        acquirer = acquire_node_dir_lock
    app = locker._app
    node_dir = app.app_node_.node_.node_dir_
    app.app_trace_.record_info('locker.acquire.begin', f'node_dir={node_dir}')
    try:
        lock_path = acquirer(node_dir)
        locker._lock_path = str(lock_path)
        app.app_trace_.record_info('locker.acquire.ok', f'lock_path={lock_path}')
    except LockError as exc:
        app.result_.set_status(Result.Status.LOCKED)
        app.app_trace_.record_error('locker.acquire.fail', exc)
        raise
```

### platform/shell/component/locker/internal/_acquire_node_dir_lock.py
```
"""acquire_lock.py
Responsible for one thing: atomically acquiring an exclusive file lock
on a node directory.  Raises LockError when the node is already locked.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from datetime import datetime, timezone

from shell.utils.path.path import PathType
from shell.component.locker.internal._is_stale import _is_stale
from shell.component.locker.internal._lock_error import LockError

LOCK_FILE = "agent.lock"
_STALE_RETRY_DELAY = 0.05


def acquire_node_dir_lock(
    node: PathType,
    clock: Callable[[], datetime] | None = None,
    get_pid: Callable[[], int] | None = None,
    sleep: Callable[[float], None] | None = None,
    create_file: Callable[[PathType, dict], None] | None = None,
    remove_file: Callable[[PathType], None] | None = None,
) -> PathType:
    """Create an atomic lock file and return its path.

    Detects and clears stale locks (process no longer exists).
    Raises LockError if the node is actively locked.
    clock:       optional callable () -> datetime (defaults to datetime.now(utc)).
    get_pid:     optional callable () -> int (defaults to os.getpid).
    sleep:       optional callable (seconds: float) -> None (defaults to time.sleep).
    create_file: optional callable (path: PathType, payload: dict) -> None, must raise
                 FileExistsError when the file already exists (defaults to atomic os.open).
    remove_file: optional callable (path: PathType) -> None (defaults to Path.unlink).
    """
    if clock is None:
        clock = lambda: datetime.now(timezone.utc)
    if get_pid is None:
        get_pid = os.getpid
    if sleep is None:
        sleep = time.sleep
    if create_file is None:
        def create_file(path: PathType, data: dict) -> None:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False)
    if remove_file is None:
        remove_file = Path.unlink

    lock_path = node / LOCK_FILE
    payload = {
        "pid": get_pid(),
        "timestamp": clock().isoformat(),
    }

    for _ in range(2):
        try:
            create_file(lock_path, payload)
            return lock_path
        except FileExistsError:
            if _is_stale(lock_path):
                try:
                    remove_file(lock_path)
                except FileNotFoundError:
                    pass
                sleep(_STALE_RETRY_DELAY)
                continue
            raise LockError(f"Node is locked by another process: {node}")

    raise LockError(f"Node is locked: {node}")
```

### platform/shell/component/locker/internal/_assert_lock_path_set.py
```
"""_assert_lock_path_set.py
Responsible for one thing: raising ValueError when _lock_path is not set.
"""


def _assert_lock_path_set(lock_path) -> None:
    """Raise ValueError if lock_path is falsy."""
    if not lock_path:
        raise ValueError("[Lock] _lock_path is not set")
```

### platform/shell/component/locker/internal/_is_stale.py
```
"""_is_stale.py
Private. Responsible for one thing: determining whether a lock file is stale
(i.e. the owning process no longer exists).
"""

import json

from shell.component.locker.internal._pid_alive import _pid_alive
from shell.utils.path.path import Path, PathType


def _is_stale(lock_path: PathType) -> bool:
    try:
        data = json.loads(Path.read_text(lock_path))
    except (OSError, ValueError):
        return False
    pid = data.get("pid")
    if not isinstance(pid, int) or pid <= 0:
        return True
    return not _pid_alive(pid)
```

### platform/shell/component/locker/internal/_lock_error.py
```
class LockError(RuntimeError):
    """Raised when the node is already locked by another live process."""
```

### platform/shell/component/locker/internal/_pid_alive.py
```
"""_pid_alive.py
Private. Responsible for one thing: checking whether a process with the given
PID is currently alive. Cross-platform: Win32 via ctypes, POSIX via os.kill.
"""

import os


def _pid_alive(pid: int) -> bool:
    """Return True if the process with the given PID is alive, False otherwise."""
    import sys
    if sys.platform == "win32":
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid
        )
        if not handle:
            return False
        exit_code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
        ctypes.windll.kernel32.CloseHandle(handle)
        return exit_code.value == STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True
```

### platform/shell/component/locker/internal/_release_node_dir_lock.py
```
"""release_lock.py
Responsible for one thing: releasing (deleting) the node lock file.
Safe to call even when the file has already been removed.
"""

from __future__ import annotations

from shell.utils.path.path import PathType


from collections.abc import Callable


def release_node_dir_lock(
    lock_path: PathType,
    remover: Callable[[PathType], None] | None = None,
) -> None:
    """Delete lock_path (best-effort, never raises).

    remover: optional callable (path: PathType) -> None for testability.
    """
    if remover is None:
        remover = Path.unlink
    try:
        remover(lock_path)
    except FileNotFoundError:
        pass
    except OSError:
        pass
```

### platform/shell/component/locker/locker.py
```
from __future__ import annotations

from shell.utils.path.path import Path, PathType
from collections.abc import Callable

from shell.component.locker.internal._acquire_locker import _acquire_locker
from shell.component.locker.internal._release_node_dir_lock import release_node_dir_lock
from shell.component.locker.internal._assert_lock_path_set import _assert_lock_path_set


class Locker:
    """Locker manager for a single node run."""

    __slots__ = ("_app", "_lock_path")

    def __init__(self, app) -> None:
        self._app = app
        self._lock_path: str | None = None

    @property
    def lock_path_(self) -> PathType:
        """Return the resolved lock path. Raises if not set."""
        _assert_lock_path_set(self._lock_path)
        return Path.new(self._lock_path).resolve()

    def lock_(self, locker: Callable[[PathType], PathType] | None = None) -> None:
        _acquire_locker(self, acquirer=locker)

    def unlock(self) -> None:
        """Release the node lock stored in lock_path.

        No-op when lock_path is not set (lock was never acquired).
        """
        if not self._lock_path:
            return
        release_node_dir_lock(Path.new(self._lock_path))
```

### platform/shell/component/manifest/__init__.py
```
```

### platform/shell/component/manifest/internal/__init__.py
```
```

### platform/shell/component/manifest/internal/_assert_manifest_body_loaded.py
```
"""_assert_manifest_body_loaded.py
Responsible for one thing: raising ValueError when manifest_file_body is empty.
"""


def _assert_manifest_body_loaded(body: str) -> None:
    """Raise ValueError if manifest body is empty (init_manifest not called)."""
    if not body.strip():
        raise ValueError("[Manifest] manifest_file_body is empty — call init_manifest() first")
```

### platform/shell/component/manifest/internal/_assert_manifest_not_empty.py
```
"""_assert_manifest_not_empty.py
Responsible for one thing: raising ValueError when manifest.yaml content is empty.
"""


def _assert_manifest_not_empty(body: str, manifest_path) -> None:
    """Raise ValueError if manifest YAML body is blank."""
    if not body.strip():
        raise ValueError(f"[Manifest.load] manifest.yaml is empty: '{manifest_path}'")
```

### platform/shell/component/manifest/internal/_assert_manifest_path_set.py
```
"""_assert_manifest_path_set.py
Responsible for one thing: raising ValueError when _manifest_path is not set.
"""


def _assert_manifest_path_set(path) -> None:
    """Raise ValueError if manifest path is falsy."""
    if not path:
        raise ValueError("[Manifest] _manifest_path is not set")
```

### platform/shell/component/manifest/internal/_load_manifest.py
```

from shell.component.manifest.manifest import Manifest
from shell.utils.path.path import Path, PathType
from shell.constants.constants import MANIFEST_YAML


def _load_manifest(app, reader=None) -> None:
    if reader is None:
        reader = Path.read_text
    manifest_path = app.cli_.cli_properties_.runner_root_dir_ / MANIFEST_YAML
    try:
        text: str = reader(manifest_path) or ""
    except OSError as exc:
        app.app_trace_.record_error_and_raise('manifest._load_manifest._load_manifest', exc)
    app._manifest = Manifest(app, manifest_path=manifest_path, manifest_yaml=text)
```

### platform/shell/component/manifest/internal/_manifest_description.py
```
import yaml


def get_manifest_description(app) -> str:
    """Return the 'description' field from app.manifest_ YAML text."""
    data: dict = yaml.safe_load(app.manifest_.manifest_file_body) or {}
    value = data.get("description", "")
    if not value:
        raise ValueError("[get_manifest_description] Required manifest field missing: 'description'")
    return value
```

### platform/shell/component/manifest/internal/_manifest_name.py
```
import yaml


def get_manifest_name(app) -> str:
    """Return the 'name' field from app.manifest_ YAML text."""
    data: dict = yaml.safe_load(app.manifest_.manifest_file_body) or {}
    value = data.get("name", "")
    if not value:
        raise ValueError("[get_manifest_name] Required manifest field missing: 'name'")
    return value
```

### platform/shell/component/manifest/internal/_manifest_version.py
```
import yaml


def get_manifest_version(app) -> str:
    """Return the 'version' field from app.manifest_ YAML text."""
    data: dict = yaml.safe_load(app.manifest_.manifest_file_body_) or {}
    value = data.get("version", "")
    if not value:
        raise ValueError("[get_manifest_version] Required manifest field missing: 'version'")
    return value
```

### platform/shell/component/manifest/internal/_validate_manifest.py
```
import yaml


def _validate_manifest(app) -> None:
    """Raise if any of the required manifest fields are missing from app.manifest_.

    Required: name, version, description.
    """
    data: dict = yaml.safe_load(app.manifest_.manifest_file_body) or {}
    for field in ('name', 'version', 'description'):
        if not data.get(field):
            raise ValueError(f"[_validate_manifest] Required manifest field missing: '{field}'")
```

### platform/shell/component/manifest/manifest.md
```
ten moul i ta klasa to kontener na plik manifest
```

### platform/shell/component/manifest/manifest.py
```
"""manifest.py
Manifest: structured representation of a loaded manifest.yaml file.

Fields:
    _app          — parent App (DOM back-reference)
    _manifest_path             — path to the manifest.yaml file on disk
    _manifest_file_body — raw YAML text content of that file (str)
"""

from __future__ import annotations

from shell.utils.path.path import Path, PathType

from shell.component.manifest.internal._manifest_name import get_manifest_name
from shell.component.manifest.internal._manifest_version import get_manifest_version
from shell.component.manifest.internal._manifest_description import get_manifest_description
from shell.component.manifest.internal._assert_manifest_body_loaded import _assert_manifest_body_loaded
from shell.component.manifest.internal._assert_manifest_path_set import _assert_manifest_path_set
from shell.component.manifest.internal._assert_manifest_not_empty import _assert_manifest_not_empty
from shell.constants.constants import MANIFEST_YAML


class Manifest:
    """Raw manifest data for a single node run.

    Constructed as Manifest(app) — held as app.manifest_, the canonical
    source of manifest data for the entire run.
    """

    __slots__ = ("_app", "_manifest_path", "_manifest_file_body")

    def __init__(
        self,
        app=None,
        manifest_path: PathType | str | None = None,
        manifest_file_body: str | None = None,
    ) -> None:
        self._app = app
        self._manifest_path: PathType | None = Path.new(manifest_path) if manifest_path else None
        self._manifest_file_body: str = manifest_file_body or ""

    # ------------------------------------------------------------------ #
    # Validated properties                                                 #
    # ------------------------------------------------------------------ #

    @property
    def manifest_file_body_(self) -> str:
        """Return manifest YAML text. Raises if empty (init_manifest not called)."""
        _assert_manifest_body_loaded(self._manifest_file_body)
        return self._manifest_file_body

    @property
    def manifest_path_(self) -> PathType:
        """Return the resolved manifest path. Raises if not set."""
        _assert_manifest_path_set(self._manifest_path)
        return Path.new(self._manifest_path).resolve()

    # ------------------------------------------------------------------ #
    # Properties                                                           #
    # ------------------------------------------------------------------ #

    @property
    def _manifest_name_(self) -> str:
        return get_manifest_name(self._app)

    @property
    def manifest_version_(self) -> str:
        return get_manifest_version(self._app)

    @property
    def _manifest_description_(self) -> str:
        return get_manifest_description(self._app)

    # ------------------------------------------------------------------ #
    # DOM operation                                                        #
    # ------------------------------------------------------------------ #

    def init_manifest(self, reader=None) -> None:
        """Read manifest.yaml from the runner root and store raw text on self.

        reader: optional callable (path: PathType) -> str for testability.
        """
        if reader is None:
            reader = lambda p: p.read_text(encoding='utf-8')  # noqa: E731
        manifest_path = self._app.cli_.cli_properties_.runner_root_dir_ / MANIFEST_YAML
        try:
            self._manifest_path = manifest_path
            self._manifest_file_body = reader(manifest_path) or ""
            _assert_manifest_not_empty(self._manifest_file_body, manifest_path)
        except Exception as exc:
            self._app.app_trace_.record_error_and_raise('manifest.Manifest.init_manifest', exc)
```

### platform/shell/component/message/__init__.py
```
from shell.component.message.message.message import Message
from shell.component.message.message_envelope.message_envelope import MessageEnvelope
from shell.component.message.message_formatter.message_formatter import MessageFormatter
from shell.component.message.message_list.message_list import MessageList
from shell.component.message.message_meta.message_meta import MessageMeta
from shell.component.message.message_reader.message_reader import MessageReader
from shell.component.message.message_status.message_status import MessageStatus
from shell.component.message.message_type.message_type import MessageType
from shell.component.message.message_validator.message_validator import MessageValidator
from shell.component.message.message_name.message_name import MessageName
from shell.component.message.message_writer.message_writer import MessageWriter
from shell.component.message.source_type.source_type import SourceType
```

### platform/shell/component/message/message/__init__.py
```
from shell.component.message.message.message import Message
```

### platform/shell/component/message/message/internal/_from_envelope.py
```
from __future__ import annotations


def _from_envelope(envelope: object, source_name: str, source_type: object) -> object:
    from shell.component.message.message.message import Message
    from shell.component.message.message_status.message_status import MessageStatus

    message = Message()
    message._message_envelope = envelope
    message._source_name = source_name
    message._source_type = source_type
    message._status = MessageStatus.CREATED
    return message
```

### platform/shell/component/message/message/message.py
```
from __future__ import annotations

from shell.component.message.message.internal._from_envelope import _from_envelope
from shell.component.message.message_envelope.message_envelope import MessageEnvelope
from shell.component.message.message_status.message_status import MessageStatus
from shell.component.message.source_type.source_type import SourceType


class Message:
    """
    Slots:
        _message_envelope — message envelope
        _source_name      — Optional; source name (full path or other identifier)
        _source_type      — Optional; source type
        _status           — Optional; message status
    """

    __slots__ = ("_message_envelope", "_source_name", "_source_type", "_status")

    def __init__(self) -> None:
        self._message_envelope: MessageEnvelope | None = None
        self._source_name: str | None = None
        self._source_type: SourceType | None = None
        self._status: MessageStatus | None = None

    @property
    def message_envelope_(self) -> MessageEnvelope:
        return self._message_envelope

    @property
    def source_name_(self) -> str | None:
        return self._source_name

    @property
    def source_type_(self) -> SourceType | None:
        return self._source_type

    @property
    def status_(self) -> MessageStatus | None:
        return self._status

    @staticmethod
    def from_envelope(envelope: MessageEnvelope, source_name: str, source_type: SourceType) -> Message:
        return _from_envelope(envelope, source_name, source_type)
```

### platform/shell/component/message/message.md
```
Realizuje element bezposredniej komunikacji miedzy elementami grafu.
Przesyla komendy zapytania itp
```

### platform/shell/component/message/message_envelope/__init__.py
```
from shell.component.message.message_envelope.message_envelope import MessageEnvelope
```

### platform/shell/component/message/message_envelope/internal/_assert_envelope_fields.py
```
from __future__ import annotations


def _assert_envelope_fields(data: dict) -> None:
    if "meta" not in data:
        raise ValueError("[MessageEnvelope] missing required section 'meta'")
    if "payload" not in data:
        raise ValueError("[MessageEnvelope] missing required field 'payload'")
```

### platform/shell/component/message/message_envelope/internal/_from_meta_and_payload.py
```
from __future__ import annotations


def _from_meta_and_payload(message_meta: object, payload: str) -> object:
    from shell.component.message.message_envelope.message_envelope import MessageEnvelope

    envelope = MessageEnvelope()
    envelope._message_meta = message_meta
    envelope._payload = payload
    return envelope
```

### platform/shell/component/message/message_envelope/internal/_init_envelope_data.py
```
from __future__ import annotations

from shell.component.message.message_envelope.internal._assert_envelope_fields import _assert_envelope_fields
from shell.component.message.message_meta.message_meta import MessageMeta


def _init_envelope_data(envelope: object, data: dict) -> None:
    _assert_envelope_fields(data)

    meta = MessageMeta()
    meta.init_meta_data(data.get("meta", {}))
    envelope._message_meta = meta
    envelope._payload = data.get("payload")
```

### platform/shell/component/message/message_envelope/internal/_to_dict.py
```
from __future__ import annotations


def _to_dict(envelope: object) -> dict:
    return {
        "meta": envelope.message_meta_.to_dict(),
        "payload": envelope.payload_,
    }
```

### platform/shell/component/message/message_envelope/message_envelope.py
```
from __future__ import annotations

from shell.component.message.message_envelope.internal._from_meta_and_payload import _from_meta_and_payload
from shell.component.message.message_envelope.internal._init_envelope_data import _init_envelope_data
from shell.component.message.message_envelope.internal._to_dict import _to_dict
from shell.component.message.message_meta.message_meta import MessageMeta


class MessageEnvelope:
    """
    Slots:
        _message_meta — message metadata
        _payload      — message payload
    """

    __slots__ = ("_message_meta", "_payload")

    def __init__(self) -> None:
        self._message_meta: MessageMeta | None = None
        self._payload: str | None = None

    @property
    def message_meta_(self) -> MessageMeta:
        return self._message_meta

    @property
    def payload_(self) -> str:
        return self._payload

    def init_envelope_data(self, data: dict) -> None:
        _init_envelope_data(self, data)

    def to_dict(self) -> dict:
        return _to_dict(self)

    @staticmethod
    def from_meta_and_payload(message_meta: MessageMeta, payload: str) -> MessageEnvelope:
        return _from_meta_and_payload(message_meta, payload)
```

### platform/shell/component/message/message_formatter/__init__.py
```
from shell.component.message.message_formatter.message_formatter import MessageFormatter
```

### platform/shell/component/message/message_formatter/internal/_assert_message_meta_set.py
```
from __future__ import annotations


def _assert_message_meta_set(message_meta) -> None:
    if message_meta is None:
        raise ValueError("[MessageFormatter] message_meta is required for plain text files")
```

### platform/shell/component/message/message_formatter/internal/_format_message_file.py
```
from __future__ import annotations

import yaml

from shell.component.message.message.message import Message
from shell.component.message.message_envelope.message_envelope import MessageEnvelope
from shell.component.message.message_formatter.internal._assert_message_meta_set import _assert_message_meta_set
from shell.component.message.message_meta.message_meta import MessageMeta
from shell.component.message.message_reader.message_reader import MessageReader
from shell.component.message.source_type.source_type import SourceType
from shell.utils.path.path import Path


def _format_message_file(formatter: object, message_meta: MessageMeta | None) -> Message:
    path = formatter.path_
    raw = Path.read_text(path)

    is_message_file = False
    try:
        data = yaml.safe_load(raw)
        if isinstance(data, dict) and "meta" in data and "payload" in data:
            is_message_file = True
    except Exception:
        pass

    if is_message_file:
        reader = MessageReader()
        reader._path = path
        return reader.read_message_file()

    _assert_message_meta_set(message_meta)

    envelope = MessageEnvelope.from_meta_and_payload(message_meta, raw)

    return Message.from_envelope(envelope, str(path), SourceType.FILE)
```

### platform/shell/component/message/message_formatter/message_formatter.py
```
from __future__ import annotations

from shell.component.message.message.message import Message
from shell.component.message.message_formatter.internal._format_message_file import _format_message_file
from shell.component.message.message_meta.message_meta import MessageMeta
from shell.utils.path.path import PathType


class MessageFormatter:
    """
    Slots:
        _path — path to the file to format
    """

    __slots__ = ("_path",)

    def __init__(self) -> None:
        self._path: PathType | None = None

    @property
    def path_(self) -> PathType:
        return self._path

    def format_message_file(self, message_meta: MessageMeta | None = None) -> Message:
        return _format_message_file(self, message_meta)
```

### platform/shell/component/message/message_list/__init__.py
```
from shell.component.message.message_list.message_list import MessageList
```

### platform/shell/component/message/message_list/internal/_assert_single_message_by_status.py
```
from __future__ import annotations

from shell.component.message.message_status.message_status import MessageStatus


def _assert_single_message_by_status(matches: list, status: MessageStatus) -> None:
    if len(matches) != 1:
        raise ValueError(f"[MessageList] expected exactly one message with status '{status}', found {len(matches)}")
```

### platform/shell/component/message/message_list/message_list.py
```
from __future__ import annotations

from shell.component.message.message.message import Message
from shell.component.message.message_list.internal._assert_single_message_by_status import _assert_single_message_by_status
from shell.component.message.message_status.message_status import MessageStatus


class MessageList:
    """
    Slots:
        _messages — list of messages
    """

    __slots__ = ("_messages",)

    def __init__(self) -> None:
        self._messages: list[Message] | None = None

    @property
    def messages_(self) -> list[Message]:
        if self._messages is None:
            self._messages = []
        return self._messages

    def append_message(self, message: Message) -> None:
        self.messages_.append(message)

    def get_message_by_status(self, status: MessageStatus) -> Message:
        matches = [m for m in self.messages_ if m.status_ == status]
        _assert_single_message_by_status(matches, status)
        return matches[0]
```

### platform/shell/component/message/message_meta/__init__.py
```
from shell.component.message.message_meta.message_meta import MessageMeta
```

### platform/shell/component/message/message_meta/internal/_assert_meta_data_fields.py
```
from __future__ import annotations

_REQUIRED_FIELDS = (
    "session_id",
    "task_id",
    "message_id",
    "sender_node",
    "target_node",
    "message_type",
    "status",
    "created_at",
    "sequence_id",
    "payload",
)


def _assert_meta_data_fields(data: dict) -> None:
    for field in _REQUIRED_FIELDS:
        if field not in data:
            raise ValueError(f"[MessageMeta] missing required field '{field}' in meta section")
```

### platform/shell/component/message/message_meta/internal/_assert_response_type_mapped.py
```
from __future__ import annotations


def _assert_response_type_mapped(response_type, message_type) -> None:
    if response_type is None:
        raise ValueError(f"[MessageMeta] no response mapping for message_type: '{message_type}'")
```

### platform/shell/component/message/message_meta/internal/_init_meta_data.py
```
from __future__ import annotations

from shell.component.message.message_meta.internal._assert_meta_data_fields import _assert_meta_data_fields
from shell.component.message.message_status.message_status import MessageStatus
from shell.component.message.message_type.message_type import MessageType


def _init_meta_data(meta: object, data: dict) -> None:
    _assert_meta_data_fields(data)

    meta._session_id = data.get("session_id")
    meta._task_id = data.get("task_id")
    meta._parent_task_ids = data.get("parent_task_ids")
    meta._message_id = data.get("message_id")
    meta._parent_message_id = data.get("parent_message_id")
    meta._sender_node = data.get("sender_node")
    meta._target_node = data.get("target_node")
    meta._message_type = MessageType(data["message_type"]) if data.get("message_type") else None
    meta._status = MessageStatus(data["status"]) if data.get("status") else None
    meta._created_at = data.get("created_at")
    meta._sequence_id = data.get("sequence_id")
    meta._payload = data.get("payload")
```

### platform/shell/component/message/message_meta/internal/_reverse_message_meta.py
```
from __future__ import annotations

from datetime import datetime, timezone

from shell.component.message.message_meta.internal._assert_response_type_mapped import _assert_response_type_mapped
from shell.component.message.message_status.message_status import MessageStatus
from shell.component.message.message_type.message_type import MessageType

_RESPONSE_TYPE_MAP = {
    MessageType.EVENT: MessageType.ACK,
    MessageType.COMMAND: MessageType.EXECUTED,
    MessageType.REQUEST: MessageType.RESPONSE,
    MessageType.RESPONSE: MessageType.OK,
    MessageType.ACK: MessageType.OK,
}


def _reverse_message_meta(input_meta: object) -> object:
    from shell.component.message.message_meta.message_meta import MessageMeta

    response_type = _RESPONSE_TYPE_MAP.get(input_meta.message_type_)
    _assert_response_type_mapped(response_type, input_meta.message_type_)

    now = datetime.now(timezone.utc).isoformat()

    meta = MessageMeta()
    meta._session_id = input_meta.session_id_
    meta._task_id = input_meta.task_id_
    meta._parent_task_ids = input_meta.parent_task_ids_
    meta._message_id = now
    meta._parent_message_id = input_meta.message_id_
    meta._sender_node = input_meta.target_node_
    meta._target_node = input_meta.sender_node_
    meta._message_type = response_type
    meta._status = MessageStatus.PENDING
    meta._created_at = now
    meta._sequence_id = (input_meta.sequence_id_ or 0) + 1
    meta._payload = None

    return meta
```

### platform/shell/component/message/message_meta/internal/_to_dict.py
```
from __future__ import annotations


def _to_dict(meta: object) -> dict:
    return {
        "session_id": meta.session_id_,
        "task_id": meta.task_id_,
        "parent_task_ids": meta.parent_task_ids_,
        "message_id": meta.message_id_,
        "parent_message_id": meta.parent_message_id_,
        "sender_node": meta.sender_node_,
        "target_node": meta.target_node_,
        "message_type": meta.message_type_.value if meta.message_type_ else None,
        "status": meta.status_.value if meta.status_ else None,
        "created_at": meta.created_at_,
        "sequence_id": meta.sequence_id_,
        "payload": meta.payload_,
    }
```

### platform/shell/component/message/message_meta/message_meta.py
```
from __future__ import annotations

from shell.component.message.message_meta.internal._init_meta_data import _init_meta_data
from shell.component.message.message_meta.internal._reverse_message_meta import _reverse_message_meta
from shell.component.message.message_meta.internal._to_dict import _to_dict
from shell.component.message.message_status.message_status import MessageStatus
from shell.component.message.message_type.message_type import MessageType


class MessageMeta:
    """
    Slots:
        _session_id        — session identifier
        _task_id           — task identifier
        _parent_task_ids   — Optional; list of parent task identifiers
        _message_id        — message identifier
        _parent_message_id — Optional; parent message identifier
        _sender_node       — sender node name
        _target_node       — target node name
        _message_type      — message type
        _status            — message status
        _created_at        — creation timestamp
        _sequence_id       — sequence number
        _payload           — message payload
    """

    __slots__ = (
        "_session_id",
        "_task_id",
        "_parent_task_ids",
        "_message_id",
        "_parent_message_id",
        "_sender_node",
        "_target_node",
        "_message_type",
        "_status",
        "_created_at",
        "_sequence_id",
        "_payload",
    )

    def __init__(self) -> None:
        self._session_id: str | None = None
        self._task_id: str | None = None
        self._parent_task_ids: list[str] | None = None
        self._message_id: str | None = None
        self._parent_message_id: str | None = None
        self._sender_node: str | None = None
        self._target_node: str | None = None
        self._message_type: MessageType | None = None
        self._status: MessageStatus | None = None
        self._created_at: str | None = None
        self._sequence_id: int | None = None
        self._payload: str | None = None

    @property
    def session_id_(self) -> str:
        return self._session_id

    @property
    def task_id_(self) -> str:
        return self._task_id

    @property
    def parent_task_ids_(self) -> list[str] | None:
        return self._parent_task_ids

    @property
    def message_id_(self) -> str:
        return self._message_id

    @property
    def parent_message_id_(self) -> str | None:
        return self._parent_message_id

    @property
    def sender_node_(self) -> str:
        return self._sender_node

    @property
    def target_node_(self) -> str:
        return self._target_node

    @property
    def message_type_(self) -> MessageType:
        return self._message_type

    @property
    def status_(self) -> MessageStatus:
        return self._status

    @property
    def created_at_(self) -> str:
        return self._created_at

    @property
    def sequence_id_(self) -> int:
        return self._sequence_id

    @property
    def payload_(self) -> str:
        return self._payload

    def init_meta_data(self, data: dict) -> None:
        _init_meta_data(self, data)

    def to_dict(self) -> dict:
        return _to_dict(self)

    @staticmethod
    def reverse_message_meta(input_meta: MessageMeta) -> MessageMeta:
        return _reverse_message_meta(input_meta)
```

### platform/shell/component/message/message_name/__init__.py
```
from shell.component.message.message_name.message_name import MessageName
```

### platform/shell/component/message/message_name/internal/_format_name.py
```
from __future__ import annotations

from shell.component.message.message_meta.message_meta import MessageMeta


def _format_name(message_meta: MessageMeta) -> str:
    parts = [
        str(message_meta.session_id_),
        str(message_meta.task_id_),
        str(message_meta.message_id_),
        str(message_meta.sender_node_),
        str(message_meta.target_node_),
        str(message_meta.message_type_.value),
        str(message_meta.status_.value),
        str(message_meta.sequence_id_),
    ]
    return "_".join(parts) + ".json"
```

### platform/shell/component/message/message_name/internal/_rename_message.py
```
from __future__ import annotations

from shell.component.message.message_meta.message_meta import MessageMeta
from shell.component.message.message_name.internal._format_name import _format_name
from shell.utils.path.path import Path, PathType


def _rename_message(path: PathType, meta: MessageMeta) -> PathType:
    new_name = _format_name(meta)
    new_path = Path.new(path.parent, new_name)
    Path.move(path, new_path)
    return new_path
```

### platform/shell/component/message/message_name/internal/_validate_name.py
```
from __future__ import annotations

from shell.component.message.message_meta.message_meta import MessageMeta
from shell.component.message.message_name.internal._format_name import _format_name


def _validate_name(name: str, meta: MessageMeta) -> bool:
    return name == _format_name(meta)
```

### platform/shell/component/message/message_name/message_name.py
```
from __future__ import annotations

from shell.component.message.message_meta.message_meta import MessageMeta
from shell.component.message.message_name.internal._format_name import _format_name
from shell.component.message.message_name.internal._rename_message import _rename_message
from shell.component.message.message_name.internal._validate_name import _validate_name
from shell.utils.path.path import PathType


class MessageName:

    @staticmethod
    def format_name(meta: MessageMeta) -> str:
        return _format_name(meta)

    @staticmethod
    def is_valid_name(name: str, meta: MessageMeta) -> bool:
        return _validate_name(name, meta)

    @staticmethod
    def rename_message(path: PathType, meta: MessageMeta) -> PathType:
        return _rename_message(path, meta)
```

### platform/shell/component/message/message_reader/__init__.py
```
from shell.component.message.message_reader.message_reader import MessageReader
```

### platform/shell/component/message/message_reader/internal/_read_message_file.py
```
from __future__ import annotations

import yaml

from shell.component.message.message.message import Message
from shell.component.message.message_envelope.message_envelope import MessageEnvelope
from shell.component.message.source_type.source_type import SourceType


def _read_message_file(reader: object) -> Message:
    raw = reader.path_.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)

    envelope = MessageEnvelope()
    envelope.init_envelope_data(data)

    message = Message()
    message._message_envelope = envelope
    message._source_name = str(reader.path_)
    message._source_type = SourceType.FILE

    return message
```

### platform/shell/component/message/message_reader/message_reader.py
```
from __future__ import annotations

from shell.component.message.message.message import Message
from shell.component.message.message_reader.internal._read_message_file import _read_message_file
from shell.utils.path.path import Path, PathType


class MessageReader:
    """
    Slots:
        _path — path to the message file
    """

    __slots__ = ("_path",)

    def __init__(self) -> None:
        self._path: PathType | None = None

    @property
    def path_(self) -> PathType:
        return self._path

    def read_message_file(self) -> Message:
        return _read_message_file(self)

    @staticmethod
    def read(path: PathType) -> Message:
        reader = MessageReader()
        reader._path = path
        return reader.read_message_file()
```

### platform/shell/component/message/message_status/__init__.py
```
from shell.component.message.message_status.message_status import MessageStatus
```

### platform/shell/component/message/message_status/message_status.py
```
from __future__ import annotations

from enum import Enum


class MessageStatus(str, Enum):
    CREATED = "created"
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
```

### platform/shell/component/message/message_type/__init__.py
```
from shell.component.message.message_type.message_type import MessageType
```

### platform/shell/component/message/message_type/message_type.py
```
from __future__ import annotations

from enum import Enum


class MessageType(str, Enum):
    EVENT = "event"
    COMMAND = "command"
    REQUEST = "request"
    RESPONSE = "response"
    ACK = "ack"
    EXECUTED = "executed"
    OK = "ok"
    TASK = "task"
    DONE = "done"
```

### platform/shell/component/message/message_validator/__init__.py
```
```

### platform/shell/component/message/message_validator/internal/_assert_message_body_valid.py
```
from __future__ import annotations


def _assert_message_body_valid(body: str) -> None:
    import yaml

    if not body or not body.strip():
        raise ValueError("[MessageValidator] message body is empty")

    try:
        data = yaml.safe_load(body)
    except yaml.YAMLError as error:
        raise ValueError(f"[MessageValidator] message body is not valid YAML: {error}")

    if not isinstance(data, dict):
        raise ValueError(f"[MessageValidator] message body must be a YAML mapping, got {type(data).__name__}")

    if "meta" not in data:
        raise ValueError("[MessageValidator] message body is missing required section 'meta'")

    if "payload" not in data:
        raise ValueError("[MessageValidator] message body is missing required field 'payload'")

    meta = data["meta"]
    if not isinstance(meta, dict):
        raise ValueError(f"[MessageValidator] 'meta' must be a mapping, got {type(meta).__name__}")

    _REQUIRED_META_FIELDS = (
        "session_id",
        "task_id",
        "message_id",
        "sender_node",
        "target_node",
        "message_type",
        "status",
        "created_at",
        "sequence_id",
        "payload",
    )
    for field in _REQUIRED_META_FIELDS:
        if field not in meta:
            raise ValueError(f"[MessageValidator] meta is missing required field '{field}'")
```
