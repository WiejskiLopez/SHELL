"""init_count_files_task.py

Initializes the SQLite DB for the 'count-files' 4-agent workflow:
  analyst -> developer -> tester -> reviewer

Usage (run from repo root or anywhere):
    cd C:\\Users\\palysiewicz\\IdeaProjects\\SHELL\\platform
    python ..\\utils\\init_count_files_task.py
    python ..\\utils\\init_count_files_task.py --db-path C:\\temp\\mydb\\shell.db --work-dir C:\\temp\\count-files
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path as _Path

_REPO_ROOT = _Path(__file__).resolve().parent.parent
_PLATFORM = _REPO_ROOT / "platform"
sys.path.insert(0, str(_PLATFORM))

from shell.memory.sql_driver.sqlite_driver.sqlite_driver import SqliteDriver
from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend
from shell.task.task_schema.internal._apply_task_schema import _apply_task_schema
from shell.bus.bus_schema.internal._apply_bus_schema import _apply_bus_schema
from shell.component.runner_config_repo.internal._apply_runner_config_schema import _apply_runner_config_schema
from shell.memory.sql_memory_backend.internal._apply_schema import _apply_schema
from shell.component.node_result_repo.internal._apply_node_result_schema import _apply_node_result_schema
from shell.component.prompt_repo.internal._apply_prompt_schema import _apply_prompt_schema
from shell.task.task_repo.internal._compute_task_hash import _compute_task_hash
from shell.component.runner_config_repo.internal._compute_runner_config_hash import _compute_runner_config_hash
from shell.component.prompt_repo.internal._compute_prompt_hash import _compute_prompt_hash

_AGENT_CLI_ROOT = str(_REPO_ROOT / "agent" / "cli-agent")
_ROUTER_ROOT = str(_REPO_ROOT / "router" / "default-router")
_TASKER_ROOT = str(_REPO_ROOT / "tasker" / "default-tasker")
_DEFAULT_DB = str(_REPO_ROOT / "tasker" / "default-tasker" / ".shell" / "shell.db")
_DEFAULT_WORK_DIR = r"C:\temp\count-files"
_TASK_NAME = "count-files"

_AGENT_CONFIG_YAML = """\
name: cli-agent
mode: agent
role: agent
type: default
log_level: INFO
max_step: 20
model: gpt-5-mini
command: 'C:\\Users\\palysiewicz\\AppData\\Roaming\\npm\\copilot.cmd'
timeout: 120
retries: 0
retry_delay: 1
no_ask_user: true
autopilot: true
"""

_ROUTER_CONFIG_YAML = """\
name: default-router
mode: router
role: router
type: base
log_level: INFO
max_step: 20
"""

_TASK_MD = """\
# count-files

Napisz skrypt Python liczący pliki w podanym folderze.

## Wymagania funkcjonalne

- Skrypt przyjmuje ścieżkę do katalogu jako argument CLI (pozycyjny lub `--path`)
- Liczy wszystkie pliki rekurencyjnie (podkatalogi włącznie)
- Wyświetla wynik w formacie: `Znaleziono X plików w: <ścieżka>`
- Domyślna ścieżka: bieżący katalog (`.`)

## Wymagania techniczne

- Python 3.10+, tylko biblioteka standardowa (os, pathlib, argparse)
- Obsługa błędów: nieistniejący folder → czytelny komunikat i exit code 1
- Obsługa błędów: brak uprawnień do podkatalogu → ostrzeżenie, kontynuuj liczenie
- Skrypt wykonywalny (if __name__ == "__main__")

## Edge cases

- Puste foldery (wynik = 0)
- Folder zawiera tylko podkatalogi bez plików
- Bardzo głęboka struktura katalogów (>100 poziomów)
- Ścieżka ze spacjami

## Format outputu

```
Znaleziono 42 pliki w: C:\\Users\\jan\\projekty
```
"""


def _build_task_yaml(work_dir: str) -> str:
    return f"""\
name: {_TASK_NAME}
session_id: null

graph:

  - node_dir: {work_dir}\\nodes\\router
    runner_root_dir: {_ROUTER_ROOT}
    mode: router
    role: router
    type: base
    status: null

  - node_dir: {work_dir}\\nodes\\analyst
    runner_root_dir: {_AGENT_CLI_ROOT}
    mode: agent
    role: analyst
    model: gpt-5-mini
    type: agent
    status: null

  - node_dir: {work_dir}\\nodes\\developer
    runner_root_dir: {_AGENT_CLI_ROOT}
    mode: agent
    role: developer
    model: gpt-5-mini
    type: agent
    status: null

  - node_dir: {work_dir}\\nodes\\tester
    runner_root_dir: {_AGENT_CLI_ROOT}
    mode: agent
    role: tester
    model: gpt-5-mini
    type: agent
    status: null

  - node_dir: {work_dir}\\nodes\\reviewer
    runner_root_dir: {_AGENT_CLI_ROOT}
    mode: agent
    role: reviewer
    model: gpt-5-mini
    type: agent
    status: null
"""


_PROMPTS: dict[str, str] = {
    "analyst": """\
Jesteś analitykiem oprogramowania (Software Analyst). Twoim zadaniem jest dogłębna analiza
wymagań i przygotowanie precyzyjnej specyfikacji technicznej dla dewelopera.

## Pipeline

Pracujesz w 4-osobowym zespole agentów:
  analyst (Ty) → developer → tester → reviewer

Po ukończeniu analizy Twój wynik trafia do dewelopera.

## Twoje zadanie

1. Przeczytaj dokładnie opis zadania z wiadomości wejściowej.
2. Napisz specyfikację techniczną zawierającą:
   - Cel i zakres skryptu
   - Pełną listę wymagań funkcjonalnych
   - Interfejs CLI (argumenty, flagi, wartości domyślne)
   - Format wyjścia (stdout)
   - Kody wyjścia (exit codes)
   - Obsługę błędów i edge cases
   - Sugerowane podejście implementacyjne (moduły, funkcje)
3. Specyfikacja ma być precyzyjna i kompletna — deweloper nie powinien zgadywać.

## Format odpowiedzi

Pierwsza linia Twojej odpowiedzi MUSI brzmieć dokładnie:
TARGET: developer

Następnie (po pustej linii) umieść specyfikację techniczną w Markdown.
""",

    "developer": """\
Jesteś programistą Python (Software Developer). Twoim zadaniem jest implementacja
skryptu na podstawie specyfikacji technicznej przygotowanej przez analityka.

## Pipeline

Pracujesz w 4-osobowym zespole agentów:
  analyst → developer (Ty) → tester → reviewer

Otrzymujesz specyfikację od analityka. Po napisaniu kodu przekazujesz go testerowi.

## Twoje zadanie

1. Przeczytaj specyfikację z wiadomości wejściowej.
2. Napisz kompletny skrypt Python spełniający WSZYSTKIE wymagania ze specyfikacji.
3. Kod musi być:
   - Gotowy do uruchomienia (bez modyfikacji)
   - Zgodny z Python 3.10+, tylko stdlib
   - Czytelny i dobrze zorganizowany
4. Do odpowiedzi dołącz:
   - Pełny kod skryptu (w bloku ```python)
   - Krótkie wyjaśnienie kluczowych decyzji implementacyjnych
   - Przykłady użycia z linii poleceń

## Format odpowiedzi

Pierwsza linia Twojej odpowiedzi MUSI brzmieć dokładnie:
TARGET: tester

Następnie (po pustej linii) umieść kod i wyjaśnienia.
""",

    "tester": """\
Jesteś testerem oprogramowania (QA Engineer). Twoim zadaniem jest weryfikacja
kodu dostarczonego przez dewelopera i napisanie testów jednostkowych.

## Pipeline

Pracujesz w 4-osobowym zespole agentów:
  analyst → developer → tester (Ty) → reviewer

Otrzymujesz kod od dewelopera. Po przetestowaniu przekazujesz raport recenzentowi.

## Twoje zadanie

1. Przeczytaj kod z wiadomości wejściowej.
2. Przeprowadź code review:
   - Czy kod spełnia wymagania (z opisu zadania)?
   - Czy obsługuje edge cases?
   - Czy obsługuje błędy poprawnie?
   - Czy exit codes są właściwe?
3. Napisz testy jednostkowe (pytest):
   - Test normalnego użycia (folder z plikami)
   - Test pustego folderu
   - Test nieistniejącej ścieżki
   - Test folderu z podkatalogami
4. Wykonaj testy mentalnie lub opisz oczekiwane wyniki.
5. Wydaj werdykt: PASS / FAIL

## Format odpowiedzi

Pierwsza linia Twojej odpowiedzi MUSI brzmieć dokładnie:
TARGET: reviewer

Następnie (po pustej linii) umieść raport z testów i kod testów.
""",

    "reviewer": """\
Jesteś starszym inżynierem (Senior Reviewer). Twoim zadaniem jest finalna weryfikacja
całego procesu: specyfikacji, kodu i testów.

## Pipeline

Pracujesz w 4-osobowym zespole agentów:
  analyst → developer → tester → reviewer (Ty)

Otrzymujesz pełne wyniki pracy zespołu. Twój werdykt kończy workflow.

## Twoje zadanie

1. Przejrzyj raport testera z wiadomości wejściowej.
2. Oceń całość:
   - Czy specyfikacja była kompletna?
   - Czy kod implementuje wszystkie wymagania?
   - Czy testy są wyczerpujące?
   - Czy kod jest produkcyjnej jakości?
3. Wydaj ostateczny werdykt: APPROVED lub NEEDS_CHANGES
4. Jeśli NEEDS_CHANGES: wskaż konkretnie co wymaga poprawy i do kogo wrócić.
5. Napisz podsumowanie wykonanej pracy dla całego zespołu.

## Format odpowiedzi

Pierwsza linia Twojej odpowiedzi MUSI brzmieć dokładnie:
TARGET: tasker

Następnie (po pustej linii) umieść werdykt i podsumowanie.
""",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _apply_all_schemas(driver: SqliteDriver) -> None:
    backend = SqlMemoryBackend(driver)
    _apply_schema(backend)
    _apply_task_schema(driver)
    _apply_bus_schema(driver)
    _apply_runner_config_schema(driver)
    _apply_node_result_schema(driver)
    _apply_prompt_schema(driver)
    print("  [OK] schemas applied")


def _upsert_runner_config(driver: SqliteDriver, package_name: str, kind: str, body: str) -> None:
    content_hash = _compute_runner_config_hash(package_name, kind, body)
    rows = driver.query(
        "SELECT id, version, content_hash FROM runner_config "
        "WHERE package_name = ? AND kind = ? AND is_current = 1 LIMIT 1",
        (package_name, kind),
    )
    if rows and rows[0]["content_hash"] == content_hash:
        print(f"  [SKIP] runner_config {package_name}/{kind} unchanged")
        return
    next_version = 1
    if rows:
        next_version = int(rows[0]["version"]) + 1
        driver.execute(
            "UPDATE runner_config SET is_current = 0 WHERE package_name = ? AND kind = ?",
            (package_name, kind),
        )
    driver.execute(
        "INSERT INTO runner_config "
        "(package_name, kind, content_hash, source_uri, version, is_current, created_at) "
        "VALUES (?, ?, ?, ?, NULL, ?, 1, ?)",
        (package_name, kind, content_hash, next_version, _now()),
    )
    driver.commit()
    print(f"  [OK] runner_config {package_name}/{kind} v{next_version}")


def _upsert_task(driver: SqliteDriver, work_dir: str) -> int:
    content_hash = _compute_task_hash(_TASK_MD)

    rows = driver.query(
        "SELECT task_id, content_hash FROM task WHERE name = ? AND is_current = 1 LIMIT 1",
        (_TASK_NAME,),
    )
    if rows and rows[0]["content_hash"] == content_hash:
        task_id = rows[0]["task_id"]
        print(f"  [SKIP] task '{_TASK_NAME}' unchanged (task_id={task_id})")
        return task_id

    import yaml
    parsed = yaml.safe_load(body_yaml_raw) or {}
    yaml_dict_json = json.dumps(parsed, ensure_ascii=False)
    graph_entries = parsed.get("graph", []) or []

    next_version = 1
    if rows:
        next_version = driver.query(
            "SELECT MAX(version) as mv FROM task WHERE name = ?", (_TASK_NAME,)
        )[0]["mv"] + 1
        driver.execute(
            "UPDATE task SET is_current = 0 WHERE name = ? AND is_current = 1", (_TASK_NAME,)
        )

    driver.execute(
        "INSERT INTO task (name, version, content_hash, task_text, "
        "source_md_uri, source_yaml_uri, is_current, created_at) "
        "VALUES (?, ?, ?, ?, ?, NULL, NULL, 1, ?)",
        (_TASK_NAME, next_version, content_hash, _TASK_MD, _now()),
    )
    task_id = driver.last_insert_id()

    driver.execute(
        "INSERT INTO graph (task_id, yaml_dict_json, created_at) VALUES (?, ?, ?)",
        (task_id, yaml_dict_json, _now()),
    )
    graph_id = driver.last_insert_id()

    for position, entry in enumerate(graph_entries):
        driver.execute(
            "INSERT INTO graph_node "
            "(graph_id, position, node_dir, runner_root_dir, mode, role, type, model, "
            "command, timeout, retries, log_level, max_step, no_ask_user, autopilot, "
            "task_name, source_dir, work_dir, status_initial, extra_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                graph_id,
                position,
                entry.get("node_dir"),
                entry.get("runner_root_dir"),
                entry.get("mode"),
                entry.get("role"),
                entry.get("type", "default"),
                entry.get("model"),
                entry.get("command"),
                entry.get("timeout"),
                entry.get("retries"),
                entry.get("log_level"),
                entry.get("max_step"),
                int(entry["no_ask_user"]) if entry.get("no_ask_user") is not None else None,
                int(entry["autopilot"]) if entry.get("autopilot") is not None else None,
                entry.get("task_name"),
                entry.get("source_dir"),
                entry.get("work_dir"),
                entry.get("status"),
                json.dumps(entry.get("extra")) if entry.get("extra") else None,
            ),
        )

    driver.commit()
    print(f"  [OK] task '{_TASK_NAME}' v{next_version} (task_id={task_id}, {len(graph_entries)} nodes)")
    return task_id


def _upsert_prompts(driver: SqliteDriver, task_id: int) -> None:
    for role, body in _PROMPTS.items():
        content_hash = _compute_prompt_hash("role", role, role, body)
        rows = driver.query(
            "SELECT prompt_id, content_hash FROM prompt "
            "WHERE kind = 'role' AND name = ? AND role = ? AND is_current = 1 LIMIT 1",
            (role, role),
        )
        if rows and rows[0]["content_hash"] == content_hash:
            print(f"  [SKIP] prompt role={role} unchanged")
            continue
        next_version = 1
        if rows:
            next_version = driver.query(
                "SELECT MAX(version) as mv FROM prompt WHERE kind = 'role' AND name = ? AND role = ?",
                (role, role),
            )[0]["mv"] + 1
            driver.execute(
                "UPDATE prompt SET is_current = 0 WHERE kind = 'role' AND name = ? AND role = ?",
                (role, role),
            )
        driver.execute(
            "INSERT INTO prompt (kind, task_id, role, name, body, content_hash, "
            "source_uri, version, is_current, created_at) "
            "VALUES ('role', ?, ?, ?, ?, ?, NULL, ?, 1, ?)",
            (task_id, role, role, body, content_hash, next_version, _now()),
        )
        driver.commit()
        print(f"  [OK] prompt role={role} v{next_version}")


def _seed_initial_envelope(driver: SqliteDriver) -> None:
    rows = driver.query(
        "SELECT task_id FROM task WHERE name = ? AND is_current = 1 LIMIT 1", (_TASK_NAME,)
    )
    if not rows:
        print("  [WARN] task not found, skipping initial envelope")
        return

    rows_wf = driver.query(
        "SELECT workflow_id FROM workflow WHERE workflow_id = ? LIMIT 1", (_TASK_NAME,)
    )
    if rows_wf:
        rows_env = driver.query(
            "SELECT id FROM envelope WHERE workflow_id = ? AND source_role = 'seed' LIMIT 1",
            (_TASK_NAME,),
        )
        if rows_env:
            print(f"  [SKIP] initial envelope already exists")
            return

    if not rows_wf:
        driver.execute(
            "INSERT INTO workflow (workflow_id, root_task_id, task_id, session_id, status, started_at) "
            "VALUES (?, ?, ?, NULL, 'OPEN', ?)",
            (_TASK_NAME, _TASK_NAME, rows[0]["task_id"], _now()),
        )
        driver.commit()
        print(f"  [OK] workflow '{_TASK_NAME}' created")

    seq_rows = driver.query(
        "SELECT COALESCE(MAX(sequence_id), 0) + 1 AS next_seq FROM envelope WHERE workflow_id = ?",
        (_TASK_NAME,),
    )
    next_seq = seq_rows[0]["next_seq"] if seq_rows else 1

    payload = json.dumps({"body": _TASK_MD, "filename": "task.md"}, ensure_ascii=False)
    driver.execute(
        "INSERT INTO envelope "
        "(workflow_id, parent_envelope_id, correlation_id, source_role, sender_node_id, "
        "receiver_node_id, target_role, payload_json, sequence_id, step, status, stage, "
        "artifact_uri, created_at, updated_at) "
        "VALUES (?, NULL, NULL, 'seed', 'tasker', NULL, 'analyst', ?, ?, 0, 'REQUESTED', 'PENDING', NULL, ?, ?)",
        (_TASK_NAME, payload, next_seq, _now(), _now()),
    )
    driver.commit()
    print(f"  [OK] initial envelope seeded (target_role=analyst)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize count-files workflow DB")
    parser.add_argument("--db-path", default=_DEFAULT_DB, help=f"Path to shell.db (default: {_DEFAULT_DB})")
    parser.add_argument("--work-dir", default=_DEFAULT_WORK_DIR, help=f"Work directory for node_dirs (default: {_DEFAULT_WORK_DIR})")
    args = parser.parse_args()

    db_path = _Path(args.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"\nDB: {db_path}")
    print(f"work_dir: {args.work_dir}\n")

    driver = SqliteDriver(db_path)
    driver.connect()

    print("1. Applying schemas...")
    _apply_all_schemas(driver)

    print("\n2. Upserting runner configs...")
    _upsert_runner_config(driver, "cli-agent", "default", _AGENT_CONFIG_YAML)
    _upsert_runner_config(driver, "default-router", "base", _ROUTER_CONFIG_YAML)

    print("\n3. Upserting task + graph nodes...")
    task_id = _upsert_task(driver, args.work_dir)

    print("\n4. Upserting role prompts...")
    _upsert_prompts(driver, task_id)

    print("\n5. Seeding initial envelope...")
    _seed_initial_envelope(driver)

    print("\nDone. Run the tasker:")
    print(f"  cd {_REPO_ROOT}\\platform")
    print(f"  python -m pytest -c pytest.ini  # (optional: verify imports)")
    print(f"  cd {_REPO_ROOT}\\tasker\\default-tasker")
    print(f"  python entrypoint.py --task-name {_TASK_NAME} --source-dir {args.work_dir} --work-dir {args.work_dir}")


if __name__ == "__main__":
    main()
