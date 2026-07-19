# Plan dokończenia Scheduling

## Stan obecny

| Element | Status |
|---------|--------|
| Domain: SchedulerJob (job config) | ✅ `scheduler_definition_id`, name, job_type, interval |
| Domain: SchedulerExecution (execution record) | ✅ status, trigger_event_id, FSM (start/complete/fail/skip) |
| Domain: SchedulerJobRepository protocol | ✅ |
| Domain: SchedulerExecutionRepository protocol | ✅ (istniejący) |
| Tabela `scheduler_execution` | ⚠️ Przechowuje job config (SchedulerJob), ale brakuje `scheduler_definition_id` FK |
| Tabela `scheduler_job` (nowa) | ✅ SQL model stworzony, przechowuje execution record (SchedulerExecution) |
| SqlSchedulerJobRepository | ✅ implementuje SchedulerExecutionRepository → `scheduler_job` table |
| Mappery SchedulerExecution ↔ SchedulerJobModel | ✅ |
| Monolith UoW | ✅ SchedulerExecutionRepository → SqlSchedulerJobRepository |
| InMemoryUoW | ✅ SchedulerExecutionRepository → InMemorySchedulerExecutionRepository |
| SchedulerService | ❌ Ładuje job config z scheduler_execution table — OK, ale wymaga weryfikacji |

## Krok 1: Migracja Alembic

### 1a. Stworzyć tabelę `scheduler_job`

Nowa migracja:
```python
op.create_table(
    "scheduler_job",
    sa.Column("id", sa.String(), nullable=False),
    sa.Column("scheduler_definition_id", sa.String(), nullable=False),
    sa.Column("status", sa.String(), nullable=False, server_default="pending"),
    sa.Column("trigger_event_id", sa.String(), nullable=True),
    sa.Column("trigger_event_type", sa.String(), nullable=True),
    sa.Column("action_ref", sa.String(), nullable=True),
    sa.Column("action_ref_type", sa.String(), nullable=True),
    sa.Column("input_state", JSONB(), nullable=True),
    sa.Column("output_state", JSONB(), nullable=True),
    sa.Column("error", sa.String(), nullable=True),
    sa.Column("started_at", sa.DateTime(), nullable=True),
    sa.Column("completed_at", sa.DateTime(), nullable=True),
    sa.Column("created_at", sa.DateTime(), nullable=False),
    sa.Column("updated_at", sa.DateTime(), nullable=True),
    sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    sa.ForeignKeyConstraint(["scheduler_definition_id"], ["scheduler_definition.id"], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint("id"),
)
```

### 1b. Przywrócić kolumny w `scheduler_execution`

Obecna tabela `scheduler_execution` ma job columns (name, job_type, interval_seconds). To jest OK dla naszego modelu (SchedulerExecution = zaplanowane zadanie = job config). Ale brakuje `scheduler_definition_id` FK.

Nowa migracja powinna dodać:
```python
op.add_column("scheduler_execution", sa.Column("scheduler_definition_id", sa.String(), nullable=True))
op.create_foreign_key("fk_scheduler_execution_definition", "scheduler_execution", "scheduler_definition", ["scheduler_definition_id"], ["id"], ondelete="CASCADE")
```

## Krok 2: Naprawić SchedulerService

Plik: `shell/infrastructure/scheduling/services/scheduler_service.py`

- Obecnie używa `SqlSchedulerExecutionRepository` do ładowania job config
- Przerzucić na `SqlSchedulerExecutionRepository` który dalej działa na `scheduler_execution` table (to jest poprawne — job config tam jest)
- Upewnić się że `list_enabled()` działa przez ten repo

## Krok 3: CRUD endpoints dla SchedulerExecution

Endpointy (tag `SchedulerExecutions`):

| Endpoint | Opis |
|----------|------|
| `GET /scheduler-executions/{id}` | Pobierz execution record — query istnieje, podpiąć przez nowy `SchedulerExecutionQueryService` |
| `GET /scheduler-executions/` | Lista execution records |
| `POST /scheduler-executions/` | Utwórz nowy execution (przez `SchedulerExecution.create()`) |
| `PUT /scheduler-executions/{id}` | Update (bump updated_at) |
| `DELETE /scheduler-executions/{id}` | Soft-delete |

## Krok 4: CRUD endpoints dla SchedulerJob (job config)

Obecnie SchedulerJob endpointy (GET) działają przez `SchedulerExecutionQueryService` który czyta z `scheduler_execution` table. To jest poprawne.

Do dodania: POST/PUT/DELETE dla job config.

## Krok 5: Testy

- Unit: command handlery przez InMemoryUnitOfWork
- E2E: endpointy przez httpx + _make_app
- Integration: SQLite dla repozytoriów

## Priorytety

1. Migracja DB
2. SchedulerService fix
3. SchedulerExecution CRUD
4. SchedulerJob CRUD
5. Testy
