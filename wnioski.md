# Wnioski z analizy projektu SHELL — pełny plan działań

> **Cel dokumentu:** kompletny zapis ustaleń analizy, błędów, propozycji i planu rozwoju, tak aby kolejna sesja/agent mógł działać na podstawie tego pliku bez ponownej analizy.
> **Zakres analizy:** `platform/shell/**` + entrypointy w `agent/`, `router/`, `tasker/`, `tools/`, `worker/`. Pominięty katalog `platform/tests/`.
> **Data analizy:** 2026-05-30.

---

## 1. Architektura projektu

SHELL to hierarchiczny, wieloagentowy system orkiestracji w Pythonie, uruchamiany jednowątkowo, z komunikacją między modułami przez system plików.

### 1.1. Komponenty kluczowe
- **App** (`platform/shell/app/app/app.py`) — DOM root; holder wszystkich referencji do modułów (`AppNode`, `AppRunner`, `AppConfig`, `AppTrace`, `Result`, `Runtime`, `AppProperties`).
- **AppRunner** (`platform/shell/app/app_runner/app_runner.py`) — dispatcher mode'ów: `agent`, `router`, `tasker`, `tool`, `worker`.
- **AppNode** (`platform/shell/app/app_node/`) — nadrzędny `Node` aplikacji; trzyma `node_dir` z CLI (`--node-dir`) lub fallback `runner_root_dir / ".node"`.
- **Graph** (`platform/shell/structure/graph/graph/graph.py`) — lista `SubNode` ładowana z YAML.
- **Node** (`platform/shell/structure/node/node/node.py`) — struktura katalogów na dysku: `.node/input/`, `output/`, `stage/`, `logs/`, `config/`, ewentualnie `archive/`, `temp/`.
- **Stage** (`platform/shell/structure/stage/`) — event-store statusów wiadomości: `active`, `pending`, `history`, `ignored`, `dead`, `done`.
- **Tasker** (`platform/shell/module/tasker/`) — executor głównego taska; inicjalizuje graph, uruchamia iteracje.
- **Router** (`platform/shell/module/router/`) — routuje wiadomości między node'ami na podstawie graph order i role mappingu.
- **Agent** (`platform/shell/module/agent/`) — wykonuje pracę AI; buduje prompt, wywołuje Copilot CLI, zwraca output.
- **Worker / Tool** — pomocnicze moduły wykonawcze (mode'y `worker`, `tool`).
- **Komponenty wspólne** (`platform/shell/component/`): `cli`, `command`, `config`, `locker`, `manifest`, `message`, `placeholders`, `process`, `prompt`, `prompt_file`, `result`, `runtime`.
- **Logger** (`platform/shell/logger/logger.py`) — globalny logger.
- **Status** (`platform/shell/status/`) — `module_status`, `status` (statusy maszyny stanów).
- **UtilsPath** (`platform/shell/utils/path/`) — JEDYNY gateway do FS; metody: `mkdir`, `exists`, `is_file`, `is_dir`, `is_symlink`, `read_text`, `read_text_safe`, `write_text`, `unlink`, `rmtree`, `copy_to`, `move`, `iterdir`, `glob`, `rglob`.

### 1.2. Przepływ wykonania
1. Entrypoint (np. `tasker/default-tasker/entrypoint.py`) woła `App.init_app(mode='tasker', runner_root_dir=__file__)`.
2. `Tasker.init_graph()` wczytuje YAML, tworzy strukturę katalogów `.node/<sub_node_name>/...` dla każdego node'a w grafie.
3. Pętla iteracyjna: `Router(READY) → Agent(processes) → Router(routes responses) → ... → DONE`.
4. Komunikacja: każdy moduł czyta/pisze pliki w stage'ach swojego node'a; brak shared memory.

### 1.3. Konwencje (z `copilot-instructions.md` + `python.good_practics.md`)
- **Sloty `_<nazwa>`** prywatne, dostęp z zewnątrz **tylko** przez property `<nazwa>_`.
- **Wewnątrz klasy** też używamy property `nazwa_`, **nigdy** `_nazwa` wprost.
- `__init__` **tylko zeruje sloty** do `None`/wartości domyślnych — żadnej logiki, żadnych instancji obiektów podrzędnych.
- Obiekty podrzędne tworzone **lazy w property** — property tworzy instancję, ale **nie inicjalizuje** jej.
- Inicjalizacja w `internal/_init_<nazwa>.py`, woła ją publiczna `init_<nazwa>()`.
- `_init_*` korzysta z property, nie ze slotu.
- Walidacja slotów wymaganych: `internal/_assert_<nazwa>.py`, wywołane w property.
- **Zakaz** `if ... raise` inline w property.
- Wszystkie operacje FS przez `UtilsPath` — **zakaz** `Path.mkdir/read_text/...`, `shutil`, `os`.
- Każda akcja mogąca rzucić błąd otoczona `record_*` (przed/po).
- Brak komentarzy w metodach Pythona, a istniejące się usuwa.
- Importy zawsze na górze pliku.
- Pełne nazwy zmiennych, zero skrótów.
- Nazwy metod publicznych: `<akcja>_<na_czym>` (np. `clean_node_input`, nigdy `clean_input`).
- Nazwa funkcji w `internal/_X.py` musi być `_X`.

---

## 2. Mocne strony

1. **DOM pattern** — czysta hierarchia z back-reference `_app` w każdym module.
2. **Lazy initialization** — większość property tworzy obiekty na żądanie.
3. **Separation of concerns** — `internal/` z dedykowanymi `_init_*`, `_assert_*`, `_validate_*`.
4. **File-based communication** — agenci przez katalogi `.node/`, brak tight coupling.
5. **Comprehensive status tracking** — Stage z 6 statusami (active/pending/history/ignored/dead/done).
6. **Type hints i `Optional`** — szeroko stosowane.
7. **UtilsPath abstraction** — jeden gateway do FS (z wyjątkami do naprawienia).
8. **Spójne entrypointy** — wszystkie używają `App.init_app(mode=..., runner_root_dir=__file__)`.
9. **Konwencja `<typ>:snake_case`** dla ID node'ów (zgodne z KG-MASTER).

---

## 3. Słabe strony / dług techniczny (przegląd)

- Init logic w `__init__` zamiast lazy property (Result w App).
- Direct `_slot` access spoza klasy-właściciela (3+ miejsca).
- Status (klasa) zamiast instancji w slocie Graph.
- Brakujący import `Path` w Node, mimo użycia w property.
- Validation w property zamiast w `_assert_*` (AppRunner.mode_).
- Init logic split między `__init__` a property/init_ (Cli).
- Property robi więcej niż lazy creation (Graph._graph_path_, AppRunner.mode_).
- Brak `record_*` wokół potencjalnie błędnych akcji (Locker).
- Niepoprawny `mode` w entrypoincie default-tool.
- Runtime tworzony bez `_app`, potem `_app` ustawiany manualnie.
- Możliwe nieużywane importy (`shutil` w `_init_agent_command.py` — do potwierdzenia).
- Komentarz `_graph_path_`: „to raczej do wywalenia" — oznacza świadomy dług.

---

## 4. Lista znalezionych błędów (TOP 15) — z lokalizacją

| # | Plik | Linia (przybl.) | Typ | Opis |
|---|------|-----------------|-----|------|
| 1 | `platform/shell/app/app/app.py` | 54 | Init logic w `__init__` | `self._result = Result(self)` — powinno być `None`, `Result` tworzony lazy w property `result_` (która już istnieje). |
| 2 | `platform/shell/structure/graph/graph/graph.py` | 27 | Type error | `self._status = Status` — zapisuje klasę zamiast instancji. Powinno `None` lub `Status.NULL`. |
| 3 | `platform/shell/structure/node/node/node.py` | top | Missing import | `Path` używany w property `node_dir_`, brak `from shell.utils.path.path import Path`. |
| 4 | `tools/default-tool/entrypoint.py` | 10 | Logic error | `mode='tasker'` zamiast `mode='tool'`. |
| 5 | `platform/shell/app/app/app.py` | 61 | Direct slot access | `self._result._status = status` — pisze w prywatny slot innej klasy. Powinno: `self.result_.set_status(status)` (dodać setter). |
| 6 | `platform/shell/app/app/app.py` | 134 | Direct slot access | `self._runtime._app = self` — bezpośredni zapis cudzego slotu. Powinno: wstrzyknięcie `app` w `init_runtime` lub setter. |
| 7 | `platform/shell/component/cli/cli/cli.py` | 42 | Direct slot access | `self._cli_properties._cli = self` — jak wyżej. |
| 8 | `platform/shell/app/app_runner/app_runner.py` | 87 | Validation w property | `mode_` property robi `raise ValueError(...)`. Powinno: walidacja w `internal/_assert_mode_valid.py`, property tylko zwraca. |
| 9 | `platform/shell/component/cli/cli/cli.py` | 47-48 | Init logic w metodzie | `init_cli()` zawiera `append_config_value(...)` zamiast delegować całość do `internal/_init_cli.py`. |
| 10 | `platform/shell/component/locker/locker.py` | 41-51 | Init logic w metodzie | `lock_()` zawiera acquire logic — powinno być w `internal/_init_locker.py` lub `internal/_acquire_locker.py`. |
| 11 | `platform/shell/structure/graph/graph/graph.py` | 45 | Property robi computacje | `_graph_path_` property robi resolve+concat. Konwertuj na slot wypełniany w `_init_graph`. Komentarz autora: „do wywalenia". |
| 12 | `platform/shell/component/cli/cli/cli.py` | 31-34 | Config append w `__init__` | Wartości configu pchane w property `cli_config_` lub `__init__` zamiast w external initializer. |
| 13 | `platform/shell/module/agent/agent_command/internal/_init_agent_command.py` | ~7 | Possibly unused import | `import shutil` — sprawdzić użycie. |
| 14 | `platform/shell/structure/sub_node/sub_node_properties/sub_node_properties.py` | ~194 | Concern | `init_sub_node_properties()` — zweryfikować, czy faktycznie tylko inicjalizuje sloty. |
| 15 | `platform/shell/component/locker/` | — | Brak `record_*` | `Locker.lock_()` może rzucić `LockError` — brak `record_error/info` przed/po. Konwencja wymaga. |

---

## 5. Plan poprawek — 3 priorytety

### 5.1. Priorytet 1 — Blockers (logiczne błędy)

#### P1.1 — `App.__init__` Result lazy
- **Plik:** `platform/shell/app/app/app.py:54`
- **Zmiana:**
  - Z: `self._result: Result | None = Result(self)`
  - Na: `self._result: Result | None = None`
- **Uzasadnienie:** `result_` property już realizuje lazy creation; podwójna inicjalizacja jest niepotrzebna i łamie wzorzec.

#### P1.2 — `Graph.__init__` Status type
- **Plik:** `platform/shell/structure/graph/graph/graph.py:27`
- **Zmiana:**
  - Z: `self._status = Status`
  - Na: `self._status = None` (lub `Status.NULL` jeśli istnieje wartość domyślna)
- **Uzasadnienie:** zapisanie klasy zamiast instancji to bug — każde użycie `status_` zwraca klasę i łamie kontrakt.

#### P1.3 — `Node` brakujący import `Path`
- **Plik:** `platform/shell/structure/node/node/node.py` (nagłówek)
- **Zmiana:** dodać `from shell.utils.path.path import Path`
- **Uzasadnienie:** property `node_dir_` używa `Path` — dziś zadziała tylko jeśli inny moduł wcześniej je zaimportował przez `__init__.py`.

#### P1.4 — `default-tool` mode
- **Plik:** `tools/default-tool/entrypoint.py:10`
- **Zmiana:** `mode='tasker'` → `mode='tool'`
- **Uzasadnienie:** entrypoint deklaruje niewłaściwy tryb; `AppRunner` rozpozna go jako tasker.

#### Verification P1
- Każdy entrypoint (`agent/cli-agent`, `router/default-router`, `tasker/default-tasker`, `tools/default-tool`, `worker/default-worker`) odpalony i `App.init_app(...)` przechodzi bez `AttributeError`/`TypeError`.
- `grep -rn "self._result = Result"` w `platform/shell/app/` — zero wyników.
- `grep -rn "self._status = Status$"` w `platform/shell/structure/graph/` — zero wyników.

### 5.2. Priorytet 2 — Naruszenia konwencji

#### P2.1 — Result setter zamiast direct slot
- **Plik:** `platform/shell/app/app/app.py:61` + `platform/shell/component/result/...`
- **Zmiana:** dodać metodę `set_status(status)` w klasie `Result`; w `App` wołać `self.result_.set_status(status)`.

#### P2.2 — Runtime injection
- **Plik:** `platform/shell/app/app/app.py:134` + `platform/shell/component/runtime/...`
- **Zmiana:** `init_runtime()` przyjmuje `app` lub Runtime ma setter `set_app(app)`. Eliminacja `self._runtime._app = self`.

#### P2.3 — CliProperties injection
- **Plik:** `platform/shell/component/cli/cli/cli.py:42`
- **Zmiana:** analogicznie jak P2.2 — setter lub wstrzyknięcie w init.

#### P2.4 — `_assert_mode_valid`
- **Pliki:**
  - `platform/shell/app/app_runner/internal/_assert_mode_valid.py` (NOWY)
  - `platform/shell/app/app_runner/app_runner.py:87`
- **Zmiana:** wynieść walidację z property `mode_` do `_assert_mode_valid(mode)`. Property zwraca tylko `self._mode`. Wywołanie asserta w setterze/initializer.

#### P2.5 — `_init_cli` przejmuje całość
- **Pliki:**
  - `platform/shell/component/cli/cli/internal/_init_cli.py` (rozszerzyć)
  - `platform/shell/component/cli/cli/cli.py:31-34, 47-48`
- **Zmiana:** wszystkie `append_config_value` i logika konfiguracyjna do `_init_cli`. `init_cli()` woła tylko `_init_cli(self, ...)`.

#### P2.6 — Locker acquire wydzielenie
- **Pliki:**
  - `platform/shell/component/locker/internal/_acquire_locker.py` (NOWY)
  - `platform/shell/component/locker/locker.py:41-51`
- **Zmiana:** logika acquire'a w internal funkcji; `lock_()` woła `_acquire_locker(self)`. Otoczyć `record_error/info`.

#### Verification P2
- `grep -rn "self\._\(result\|runtime\|cli_properties\)\." platform/shell/` — wynik tylko w klasie-właścicielu.
- `grep -rn "raise " platform/shell/**/<plik>_<nazwa>.py` poza `internal/` — zero w property.

### 5.3. Priorytet 3 — Cleanup

#### P3.1 — `Graph._graph_path_` jako slot
- **Plik:** `platform/shell/structure/graph/graph/graph.py`
- **Zmiana:** zastąpić computującą property zwykłym slotem `_graph_path` wypełnianym w `internal/_init_graph.py` (resolve+concat tam się dzieje raz).

#### P3.2 — Audit `record_*`
- **Zakres:** wszystkie publiczne metody w `module/`, `component/locker/`, `component/process/`, `component/command/`, każde I/O na pliku.
- **Zmiana:** owinięcie `record_info` przed, `record_error` w `except`, `record_info` po sukcesie.

#### P3.3 — Unused imports cleanup
- **Plik:** `platform/shell/module/agent/agent_command/internal/_init_agent_command.py` + całe `internal/`
- **Zmiana:** uruchomić `ruff --select F401` lub manualny audit; usunąć unused (m.in. potencjalnie `shutil`).

#### P3.4 — Nazewnictwo metod
- **Zakres:** audit czy wszystkie publiczne metody mają formę `<akcja>_<na_czym>` (np. brak `clean_input`, ma być `clean_node_input`). Skontrolować szczególnie `Node`, `SubNode`, `Stage`.

#### P3.5 — `__init__` purity
- **Zakres:** każdy `__init__` w `platform/shell/` powinien tylko zerować sloty. Zrobić listę naruszeń przez grep `def __init__` + manualną inspekcję ciał konstruktorów.

#### Verification P3
- Smoke test pełnego cyklu: `tasker → router → agent → router → DONE`.
- `ruff check platform/shell/` (po włączeniu reguły F401, F811, F841) — czysto.

---

## 6. Konkretne zmiany — gotowe snippety

### Snippet 1 — App lazy result
```python
# platform/shell/app/app/app.py (fragment __init__)
self._result: Result | None = None  # zamiast Result(self)
```

### Snippet 2 — Graph status
```python
# platform/shell/structure/graph/graph/graph.py (fragment __init__)
self._status = None  # zamiast self._status = Status
```

### Snippet 3 — Node import
```python
# platform/shell/structure/node/node/node.py (top of file)
from shell.utils.path.path import Path
```

### Snippet 4 — default-tool
```python
# tools/default-tool/entrypoint.py
app = App.init_app(mode='tool', runner_root_dir=__file__)  # zamiast 'tasker'
```

### Snippet 5 — Result setter
```python
# platform/shell/component/result/result/result.py
def set_status(self, status: Status) -> None:
    self._status = status

# platform/shell/app/app/app.py
if status is not None:
    self.result_.set_status(status)  # zamiast self._result._status = status
```

### Snippet 6 — _assert_mode_valid
```python
# platform/shell/app/app_runner/internal/_assert_mode_valid.py
_MODES = {'agent', 'router', 'tasker', 'tool', 'worker'}

def _assert_mode_valid(mode: str | None) -> None:
    if mode is not None and mode not in _MODES:
        raise ValueError(f"mode must be one of {sorted(_MODES)!r}, got {mode!r}")
```

### Snippet 7 — _init_cli
```python
# platform/shell/component/cli/cli/internal/_init_cli.py
def _init_cli(cli: 'Cli', argv: list[str] | None = None) -> None:
    cli.cli_config_.append_config_value('runner_root_dir', cli.runner_root_dir_, 'cli')
    # ... reszta logiki przeniesiona z cli.py
```

### Snippet 8 — _acquire_locker
```python
# platform/shell/component/locker/internal/_acquire_locker.py
def _acquire_locker(locker: 'Locker') -> None:
    locker.app_.trace_.record_info('locker.acquire.begin')
    try:
        # ... acquire logic
        locker.app_.trace_.record_info('locker.acquire.ok')
    except Exception:
        locker.app_.trace_.record_error('locker.acquire.fail')
        raise
```

---

## 7. Mapa kolejności prac (sprint plan)

### Sprint 1 — Blockers (1 sesja)
1. P1.1 → P1.2 → P1.3 → P1.4 (4 zmiany w 4 plikach)
2. Smoke test wszystkich 5 entrypointów.
3. Commit: `fix: P1 blockers — lazy Result, Status instance, Path import, default-tool mode`.

### Sprint 2 — Konwencje (1-2 sesje)
4. P2.4 (`_assert_mode_valid`) — najprostsza, samodzielna.
5. P2.1, P2.2, P2.3 — direct slot access przez settery (każda klasa w osobnym commitcie).
6. P2.5 — przeniesienie logiki Cli do `_init_cli`.
7. P2.6 — wydzielenie acquire z Lockera + `record_*`.
8. Commit per zmiana, nazewnictwo: `refactor: <obszar> — <co>`.

### Sprint 3 — Cleanup (1 sesja)
9. P3.1 — `Graph._graph_path_` na slot.
10. P3.2 — audit `record_*` (najwięcej pracy, zaplanować osobno).
11. P3.3 — unused imports.
12. P3.4 — audit nazewnictwa.
13. P3.5 — audit `__init__`.

---

## 8. Dalsze kroki rozwoju (poza naprawami)

### 8.1. Krótkoterminowe
- **Logging w `init_*`** — każde `init_X` woła `record_info` z nazwą zasobu i kontekstem.
- **`init_*` audit** — sprawdzić czy każde nazywa się `init_<nazwa>`, a nie `build_*`/`setup_*`/`create_*`.

### 8.2. Średnioterminowe
- **Formalna spec YAML graph** — udokumentować schema (klucze, typy, role, kolejność).
- **JSON Schema dla `task.yaml` i node configs** — walidacja przed parsowaniem.
- **Message envelope versioning** — każdy plik wiadomości w stage'ach ma `schema_version`.
- **Refaktor Runtime** — wstrzyknięcie `app` w init zamiast post-set (zamknięcie P2.2).

### 8.3. Długoterminowe
- **Multi-run parallel support** — obecnie single-run; lokowanie node'ów per run-id.
- **Structured logging (JSON)** — łatwiejsza analiza i indexowanie do KG.
- **DSL dla tasków** — wyższy poziom abstrakcji niż surowy YAML graph.
- **Integracja z KG-MASTER** — automatyczne raportowanie node'ów/decyzji do grafu wiedzy.

### 8.4. Testy (obecnie poza zakresem)
- Snapshot tests struktury katalogów `.node/`/`stage/`.
- Integration tests pełnego cyklu `tasker→router→agent→...→DONE`.
- Coverage `internal/_init_*` (dziś niepokryte).

---

## 9. Ocena ogólna

- **Fundamenty:** solidne (DOM, lazy, file-based, UtilsPath, modularność).
- **Dług techniczny:** ~20-30%, głównie w przestrzeganiu własnych konwencji.
- **Ryzyko produkcyjne:** błędy P1 mogą powodować runtime errors w nietypowych ścieżkach (wrong mode, Status klasa, missing import). P1.4 szczególnie — `default-tool` po prostu robi nie to co powinien.
- **Maintainability:** wysoka po naprawie P1+P2; pattern jest zrozumiały i powtarzalny.
- **Rekomendacja:** zacząć od Sprint 1 (P1) — niskie ryzyko, wysoki zysk. Potem Sprint 2 systematycznie.

---

## 10. Notatki dla kolejnej sesji

- **Konwencja krytyczna:** `__init__` zerujemy, lazy w property, init w `internal/_init_*`. Naruszenia tego są największym długiem.
- **UtilsPath only** — przed dodaniem `import shutil`/`import os` w nowym kodzie: nie. Użyj `shell/utils/path/utils_path.py`.
- **`record_*` always** — przed każdą akcją mogącą rzucić błąd.
- **Workflow `.done`** — git add/commit/push + nowy branch `<N+1>_feature` w `C:\Users\palysiewicz\IdeaProjects\schell\platform`.
- **Pominięte z analizy:** cały `platform/tests/`.
- **Niezweryfikowane (wymaga ponownego sprawdzenia):** numeracja linii w tabeli z sekcji 4 — to przybliżenia, przed implementacją zweryfikować exact lines (`grep -n` lub read_file na konkretnym fragmencie).
