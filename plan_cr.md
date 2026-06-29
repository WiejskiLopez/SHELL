# Plan CR — mypy cleanup i usunięcie prymitywów z domeny

## Stan obecny (2026-06-29)

**Start**: 435 błędów mypy w 137 plikach
**Obecnie**: ~220 błędów (testy + pre-existing infra), **zero błędów w domain/**

### Co zrobione

| Zmiana | Pliki | Status |
|--------|-------|--------|
| **Konfiguracja mypy**: `mypy_path` dla `_arch_helpers`, `disable_error_code = ["type-abstract"]` dla `shell.application.*` | `shell/pyproject.toml` | ✅ |
| **Usunięcie `from_payload`** z DomainEvent + 6 eventów z `dict[str, object]` + testu architektury | `domain_event.py`, 6 eventów, `test_domain_structure.py` | ✅ |
| **Konsolidacja duplikatów VO**: `GraphNodeDefinitionId` i `GraphDefinitionId` — `ids/` pliki → re-export z agregat-lokalnych | `shell/domain/definition/value_objects/ids/` | ✅ |
| **Usunięcie nieużywanych `# type: ignore`** | ~15 plików (konftesty, `sql_alchemy_uow.py`, testy) | ✅ |
| **`ExistsResult` runtime import** — przeniesiony z ciał metod na poziom modułu | 10 InMemory repos | ✅ |
| **Handler None guardy** — dodane `if x is None: return` po `get_by_id()` | 8 handlerów | ✅ |
| **`# type: ignore[type-abstract]`** w testach | 7 plików testowych | ✅ |
| **Type args dla bare `list`/`dict`** | `unit_of_work.py`, `identity.py`, `create_graph_definition_handler.py` i inne | ✅ |
| **VO→DTO mapowanie** — `.value` w mapperach | `mappers.py`, `in_memory_query_services.py` | ✅ |

### DomainEvent — zero prymitywów (kluczowa zmiana)

Wszystkie pola `DomainEvent` zamienione z primitives na Value Objects:

| Pole | Przed | Po |
|------|-------|-----|
| `event_id` | `str` | `EventId` |
| `aggregate_id` | `str` | `AggregateId` |
| `aggregate_type` | `str` | `AggregateType` |
| `occurred_at` | `datetime` | `CreatedAt` |
| `schema_version` | `int` | `SchemaVersion` |

Nowe VOs:
- `shell/domain/platform/value_objects/event_id.py`
- `shell/domain/platform/value_objects/aggregate_id.py`
- `shell/domain/platform/value_objects/aggregate_type.py`
- `shell/domain/platform/value_objects/schema_version.py`

### Pattern `now` w eventach

- Wszystkie event `.now(now: datetime)` → `.now(now: CreatedAt)`
- Wszystkie guard clauses: `now=now` → `now=CreatedAt.from_datetime(now)` (konwersja na granicy)
- `AggregateRoot.append_event()`: ustawia `aggregate_id=AggregateId(...)`, `aggregate_type=AggregateType(...)`
- `DomainEventSerializer`: obsługuje `CreatedAt`, `SchemaVersion`, `EventId`, `AggregateId`, `AggregateType`
- Infrastruktura `.occurred_at` → `.occurred_at.value` przy zapisie do DB

### Modyfikacja plików

- `shell/domain/platform/events/domain_event.py` — base class
- `shell/domain/platform/base/aggregate_root.py` — append_event
- `shell/infrastructure/platform/serialization/event_serializer.py` — serializer
- ~12 agregatów (guard clauses): `task_execution`, `workflow`, `graph_execution`, `graph_node_execution`, `graph_node_transition_execution`, `workflow_state`, `graph_execution_state`, `graph_node_execution_state`, `session_state`, `session`, `rag_document`, `graph_definition_embedding`
- ~60 eventów (`.now()` signatures + imports)
- ~10 plików infrastruktury (`.occurred_at` → `.value`)
- Test helpery: `conftest_helpers.py`, `test_outbox.py`

## Co zostało (~220 błędów)

### Testy (~150 błędów)
Głównie testy konstruujące eventy z `now=datetime(...)` zamiast `CreatedAt.from_datetime(...)`. Wzorzec:

```python
# BEFORE (trzeba zmienić):
TaskExecutionCreatedEvent.now(now=datetime(2026, 1, 1, tzinfo=UTC))

# AFTER:
TaskExecutionCreatedEvent.now(now=CreatedAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)))
```

Pliki do poprawy (lista orientacyjna):
- `shell/tests/execution/unit/domain/test_graph_execution_state_input.py` — ✅ zrobione
- `shell/tests/execution/unit/domain/test_graph_execution_state_output.py` — ✅ zrobione
- `shell/tests/conftest_helpers.py` — ✅ zrobione
- `shell/tests/platform/unit/application/test_outbox.py` — ✅ zrobione
- `shell/tests/platform/unit/application/test_logging_event_publisher.py` — ✅ zrobione
- **Reszta**: ~30 plików testowych z podobnym patternem

### Infrastruktura (pre-existing, ~30 błędów)
- `shell\infrastructure\platform\context\grpc_interceptor.py` — dataclass replace
- `shell\infrastructure\platform\persistence\in_memory_repository.py` — TAggregate.id
- `shell\domain\platform\ports\repository_port.py` — TypeVar variance
- `shell\application\execution\query_handlers\*.py` — QueryService brak w portach
- SQLAlchemy `@declared_attr` return type (~12 plików)
- `shell\application\execution\event_handlers\graph_node_execution_worker.py` — 12 błędów (pre-existing)

### Testy architektoniczne (~10 błędów)
- `test_process_structure.py:28` — missing type args
- `test_general_conventions.py:86` — var-annotated
- `test_domain_structure.py:541` — var-annotated

## Plan dalszych prac

### Krok 1: batch testów
Uruchomić pełny test suite, iteracyjnie naprawiać testy które padają:
```bash
python -m pytest shell/tests/ -x -q --ignore=shell/tests/execution/integration ...
```

Dla każdego failing testu:
- Jeśli woła `.now(now=datetime(...))` → zmień na `CreatedAt.from_datetime(...)`
- Jeśli importuje `datetime` tylko dla tego → zachowaj (test może używać w innym miejscu)
- Jeśli konstruuje event bezpośrednio → dodaj `occurred_at=CreatedAt.from_datetime(...)`

### Krok 2: dokończyć mypy cleanup
Po naprawieniu testów:
```bash
python -m mypy --no-incremental --config-file shell/pyproject.toml shell
```

Naprawić pozostałe błędy (głównie pre-existing w infra).

### Krok 3: testy architektoniczne
Dodać testy które wyłapują regresje:
1. `test_domain_no_primitive_imports` — żadnych `datetime`, `re`, `json` itp. w `domain/`
2. `test_type_annotations_no_bare_generics` — brak gołych `list`, `dict`
3. `test_handler_get_by_id_none_check` — None guard po `get_by_id()`
4. `test_inmemory_repository_implements_protocol` — brakujące metody
5. `test_repository_methods_import_exists_result` — poprawny import

### Krok 4: walidacja końcowa
```bash
python -m mypy --no-incremental --config-file shell/pyproject.toml shell
python -m pytest shell/tests/ -q --ignore=shell/tests/execution/integration ...
```
