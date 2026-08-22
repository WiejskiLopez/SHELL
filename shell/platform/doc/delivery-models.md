# PersistenceDeliveryModels

## Cel / Co realizuje

`PersistenceDeliveryModels` (w `shell/platform/infrastructure/persistence/sql/models/persistence_delivery.py`) to typowany `NamedTuple` grupujący wszystkie platformowe modele ORM dostarczania wiadomości, zbudowane dla jednego Bounded Context (BC). Fabryka `build_persistence_delivery_models(base: type[DeclarativeBase]) -> PersistenceDeliveryModels` tworzy komplet modeli: event/message/command inbox+outbox, `audit_event`, `processed_delivery` i `worker_heartbeat` — wszystkie podpięte do przekazanego rejestru metadanych (`metadata`) danego BC.

## Problem

Model dostarczania wiadomości (outbox/inbox) jest funkcjonalnością platformową, ale tabele muszą żyć w schemacie każdego BC oddzielnie (izolacja metadanych, brak współdzielonych tabel między serwisami). Powielanie tych samych definicji kolumn w każdym BC generowałoby duplikację i rozjazd schematów. Rozwiązaniem jest zestaw fabryk, które każdorazowo definiują klasy modeli na bazie przekazanej klasy bazowej BC, oraz wspólny mixin (`InboxStateMixin`) i wspólne kolumny/indeksy operacyjne dla wszystkich inboxów.

## Realizacja techniczna

### Bundle typowany

`PersistenceDeliveryModels` jest `NamedTuple` o polach:

```python
class PersistenceDeliveryModels(NamedTuple):
    events: EventDeliveryModels
    messages: MessageDeliveryModels
    commands: CommandDeliveryModels
    audit: type[DeclarativeBase]
    processed_delivery: type[DeclarativeBase]
    worker_heartbeat: type[DeclarativeBase]
```

`build_persistence_delivery_models(base)` deleguje do osobnych fabryk:

```python
return PersistenceDeliveryModels(
    events=build_event_delivery_models(base),
    messages=build_message_delivery_models(base),
    commands=build_command_delivery_models(base),
    audit=build_audit_event_model(base),
    processed_delivery=build_processed_delivery_model(base),
    worker_heartbeat=build_worker_heartbeat_model(base),
)
```

### Fabryki outbox/inbox

Każda z trzech fabryk (`build_event_delivery_models`, `build_message_delivery_models`, `build_command_delivery_models`) zwraca `NamedTuple` z polami `outbox` i `inbox`:

```python
class EventDeliveryModels(NamedTuple):
    outbox: type[DeclarativeBase]
    inbox: type[DeclarativeBase]
```

Definiowane klasy to `OutboxEventModel`/`InboxEventModel`, `OutboxMessageModel`/`InboxMessageModel`, `OutboxCommandModel`/`InboxCommandModel` z tabelami `outbox_event`/`inbox_event`, `outbox_message`/`inbox_message`, `outbox_command`/`inbox_command`. Po utworzeniu fabryka nadaje klasom unikalne nazwy w rejestrze metadanych:

```python
OutboxEventModel.__name__ = f"{base.__name__}OutboxEventModel"
OutboxEventModel.__qualname__ = OutboxEventModel.__name__
```

Wspólne kolumny nośnika (payload):

- `id: Mapped[str]` — klucz główny,
- `event_type` / `message_type` / `command_type: Mapped[str]` — typ nośnika,
- `occurred_at: Mapped[datetime]` (`DateTime(timezone=True)`) — czas zdarzenia biznesowego,
- `payload: Mapped[dict[str, object]]` — typ `JSONB` (patrz `_compat`),
- `correlation_id` i `causation_id: Mapped[str]` — z defaultem `""` (śledzenie korelacji),
- `published_at: Mapped[datetime | None]` — tylko outbox (moment publikacji, `NULL` = niewysłany),
- `received_at: Mapped[datetime]` — tylko inbox (moment przyjęcia przez konsumenta).

`JSONB` w `shell/platform/infrastructure/persistence/sql/models/_compat.py` to alias przenośny: `JSON().with_variant(_PgJSONB(), "postgresql")`.

### InboxStateMixin — wspólny stan operacyjny

Wszystkie modele inbox dziedziczą po `InboxStateMixin` (`shell/platform/infrastructure/persistence/sql/models/mixins/inbox_state.py`), który dodaje kolumny cyklu życia i indeksy. Mixin korzysta z `declared_attr __table_args__`:

```python
@declared_attr
def __table_args__(cls: type[Any]) -> tuple[Index, ...]:
    return build_inbox_state_indexes(cls.__tablename__)
```

Kolumny mixinu:

- `status: Mapped[str]` — default `InboxStatus.PENDING.value` (jawny stan początkowy),
- `next_attempt_at: Mapped[datetime]` — default `_default_next_attempt_at()` (czas insertu, bez `NULL`),
- `lease_until: Mapped[datetime | None]` — koniec dzierżawy (claim),
- `claimed_by: Mapped[str | None]` — identyfikator procesu trzymającego dzierżawę,
- `processed_at`, `failed_at`, `last_attempted_at: Mapped[datetime | None]`,
- `retry_count: Mapped[int]` — default `0`,
- `error`, `error_code`, `error_message: Mapped[str | None]`,
- `schema_version: Mapped[int]` — default `1`.

`build_inbox_state_indexes(table_name)` zwraca dwa wspólne indeksy:

```python
Index(f"ix_{table_name}_status_next_attempt_received", "status", "next_attempt_at", "received_at"),
Index(f"ix_{table_name}_status_lease_until", "status", "lease_until"),
```

Stany w `InboxStatus` (`shell/platform/domain/value_objects/inbox_status.py`, `ValueObject` + `StrEnum`): `PENDING`, `PROCESSING`, `PROCESSED`, `RETRY`, `DEAD_LETTER`.

Uwaga: `InboxMessageModel` dodatkowo nadpisuje `__table_args__`, dodając `Index("ix_inbox_message_processed_at", "processed_at")` przed indeksami z mixinu.

### processed_delivery (deduplikacja)

`build_processed_delivery_model(base)` tworzy `ProcessedDeliveryModel` (tabela `processed_delivery`) — jawny fallback deduplikacji dla handlerów, które nie dzielą transakcji z procesorem. Unikalność `UniqueConstraint("consumer_name", "outbox_id", name="uq_processed_delivery_consumer_outbox")` gwarantuje, że ponowna dostawa tego samego rekordu outbox do tego samego konsumenta jest no-op. Kolumny: `id` (PK), `consumer_name`, `outbox_id`, `payload`, `processed_at`.

### worker_heartbeat (liveness)

`build_worker_heartbeat_model(base)` tworzy `WorkerHeartbeatModel` (tabela `worker_heartbeat`) — `worker_id: Mapped[str]` jako klucz główny (jeden wiersz na proces worker-a) oraz `last_seen_at: Mapped[datetime]`. Zapisują go `WorkerHeartbeatRecorder.beat()`; czyta go `SqlReadinessProbe` (patrz [readiness](readiness.md)).

### Rejestracja tabel w baseline

Każdy BC definiuje własną klasę bazową, np. `shell/ingestion_service/infrastructure/ingestion/persistence/sql/models/base.py`:

```python
class IngestionSqlAlchemyModelBase(SqlAlchemyModelBase):
    __abstract__ = True
    metadata = MetaData()
    registry = registry()

PERSISTENCE_DELIVERY_MODELS = build_persistence_delivery_models(IngestionSqlAlchemyModelBase)
```

(gdzie `SqlAlchemyModelBase` w `shell/platform/infrastructure/persistence/sql/models/base.py` to `DeclarativeBase`). Tak samo postępują BC: `Session`, `Definition`, `Project`, `User`, `Execution`, `Scheduling`.

Baseline (np. `shell/ingestion_service/migrations/baseline.py`) zbiera jawne tabele z `__table__` do krotki `_TABLES` i tworzy schemat tylko dla nich:

```python
async with engine.begin() as connection:
    await connection.run_sync(
        IngestionSqlAlchemyModelBase.metadata.create_all, tables=list(_TABLES)
    )
```

Dzięki temu `create_all` nie tworzy niechcianych tabel platformowych — tylko modele zdefiniowane przez dany BC (w tym bundle dostarczania).

## Kluczowe pliki

- `shell/platform/infrastructure/persistence/sql/models/persistence_delivery.py`
- `shell/platform/infrastructure/persistence/sql/models/event_delivery.py`
- `shell/platform/infrastructure/persistence/sql/models/message_delivery.py`
- `shell/platform/infrastructure/persistence/sql/models/command_delivery.py`
- `shell/platform/infrastructure/persistence/sql/models/audit_delivery.py`
- `shell/platform/infrastructure/persistence/sql/models/processed_delivery.py`
- `shell/platform/infrastructure/persistence/sql/models/worker_heartbeat.py`
- `shell/platform/infrastructure/persistence/sql/models/mixins/inbox_state.py`
- `shell/platform/infrastructure/persistence/sql/models/_compat.py`
- `shell/platform/infrastructure/persistence/sql/models/base.py`
- `shell/platform/domain/value_objects/inbox_status.py`
- `shell/ingestion_service/infrastructure/ingestion/persistence/sql/models/base.py`
- `shell/ingestion_service/migrations/baseline.py`

## Powiązane koncepcje

- [delivery-overview](delivery-overview.md)
- [transactional-outbox](transactional-outbox.md)
- [inbox-lifecycle](inbox-lifecycle.md)
- [claim-lease](claim-lease.md)
- [processed-delivery-dedup](processed-delivery-dedup.md)
- [heartbeat-lease](heartbeat-lease.md)
- [sqlalchemy-persistence](sqlalchemy-persistence.md)
