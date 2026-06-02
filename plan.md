# Plan: DB-as-Core refactor (files → archive only)

## Status — czerwiec 2026 (po wykonaniu Faza A+B+C+E+F.cleanup)

| Obszar | Stan |
|---|---|
| `SqlMemoryBackend` + `SqlDriver` (SQLite WAL) | DONE |
| Pojedynczy shared driver w App | DONE |
| `MessageBus` DB-backed | DONE |
| `WorkflowState` DB-backed | DONE |
| `EnvelopeStage` w DB | DONE |
| `TaskRepo` + `_import_task_files` | DONE |
| `EnvelopeArchiver` | DONE |
| `NodePort` (Protocol) | DONE |
| `FilesystemNodePort` (impl) | DONE |
| `DbNodePort` (impl) z scope `{workflow_id}:{node_name}:{rel_dir}` | DONE |
| `node.port_` zwraca DbNodePort z `app.memory_` + `cli.workflow_id_` | DONE |
| `NodeInput._init_node_input` przez port | DONE |
| `NodeInput.clean_node_input` przez port | DONE |
| `NodeOutput._format_node_output` przez port (inline naming, no Reader/Writer) | DONE |
| `NodeOutput.clean_node_output` przez port | DONE |
| `_validate_node` nie wymaga już filesystem `.node/input/` | DONE |
| Tasker `_materialize_envelope_to_input` — write przez `DbNodePort` receivera | DONE |
| Tasker `_publish_response_envelopes` — read przez `DbNodePort` receivera | DONE |
| Tasker `_seed_initial_envelopes` — filesystem (boundary z userem) | DONE — celowo |
| Tasker `_collect_final_outputs_to_own` — filesystem (boundary z userem) | DONE — celowo |
| CLI `--workflow-id` + `--envelope-id` + propagacja przez tasker | DONE |
| Skasowane: `MessageWriter`, `MessageReader`, `MessageFormatter`, `MessageName` | DONE |

**Pozostało (Faza D):**

| Obszar | Stan | Priorytet |
|---|---|---|
| `Config` z DB (cache hash) | direct yaml.safe_load | Faza D |
| `PromptRepo` (role/system prompts → DB) | direct Path.read_text | Faza D |
| Bootstrap `role_prompts/*.md` jednorazowo do DB | brak | Faza D |
| Subprocess: `claim_envelope_by_id(envelope_id)` zamiast `claim_next` | low | Faza E.opt |
| Manifesty: usunąć runtime `input/output/temp/stage` z deklaracji | brak | Faza F.docs |

---

## Architektura runtime (po refaktorze)

**Granice filesystem (user-side boundary):**
- Tasker root `.node/input/` — pliki dostarczone przez usera (seed bus).
- Tasker root `.node/output/` — finalny output dla usera.
- `archive/`, `log/`, deskryptory (`manifest.yaml`, `role_prompts/*.md`).

**Wszystko inne — DB:**
- Sub-node `.node/input/` (wpisywane przez tasker przez `DbNodePort`, czytane przez subprocess przez `DbNodePort`).
- Sub-node `.node/output/` (wpisywane przez subprocess przez `DbNodePort`, czytane przez tasker przez `DbNodePort`).
- Konwencja scope: `scope_id = '{workflow_id}:{node_name}:{rel_dir}'`, `entry_key = filename`.
- workflow_id propagowany przez CLI `--workflow-id`.

**Cross-process:**
- Shared `<runner_root>/.shell/shell.db` (SQLite WAL).
- Tasker → subprocess: tasker pisze envelope payload do DB scope receivera + odpala subprocess z `--workflow-id wf --envelope-id N`.
- Subprocess App: czyta `task_id` z CLI → `task_repo.get_task_by_id` (już istniało) + `cli.workflow_id_` przekazany do `Node.port_`.

---

## Zasady portu (kontrakt)

PathType jest logicznym identyfikatorem (logical key), nie ścieżką FS.
FilesystemNodePort tłumaczy 1:1 na pathlib.
DbNodePort liczy klucz względny do node_dir i mapuje do (context_type, scope_id, entry_key).

DbNodePort konwencja:
- `node_dir` jest "rootem" portu (przekazywany do `init_db_node_port`).
- `workflow_id` opcjonalny; brak → prefix `'_global'`.
- Każda operacja na ścieżce `path` liczy `rel = path.relative_to(node_dir)`.
- Plik: `scope_id = f'{wf}:{node_name}:{rel.parent.as_posix()}'`, `entry_key = rel.name`.
- Dir: `scope_id = f'{wf}:{node_name}:{rel.as_posix()}'`, marker `entry_key='.dir'`.

---

## Weryfikacja

- ✅ Wszystkie `shell.*` moduły importują się bez błędów (walk_packages, 0 fails).
- ✅ Smoke `DbNodePort`: write/read/list_files z workflow_id scoping (wf-1 widzi swoje, wf-OTHER nie widzi).
- ✅ `MessageWriter`/`Reader`/`Formatter`/`Name` — 0 wystąpień w produkcyjnym kodzie.
- ⏳ E2E `tasker → router → agent` z prawdziwym workflow — do uruchomienia osobno (wymaga skonfigurowanego runner_root + task).

---

## Faza D — Config & Prompty z DB (TODO, następna sesja)

- `ConfigRepo.import_if_changed(node_name, path) -> dict` z hash-content-versioning.
- `PromptRepo.get_role_prompt(role)`, `get_system_prompt(role)`, ładowane z `rag_document` lub `context_entry`.
- Bootstrap: jednorazowo wczytaj wszystkie `role_prompts/*.md` do DB przy starcie App (jeśli wersja w DB starsza niż na dysku).
- **Faza F**: grep `MessageWriter|MessageReader|MessageFormatter|MessageName` w kodzie produkcyjnym = 0 trafień.
