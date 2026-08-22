# Porty i Adaptery

## Cel / Co realizuje

Definiuje wzorzec Port i Adapter na granicy między warstwą aplikacji a
infrastrukturą platformy SHELL. Porty to protokoły (typing `Protocol`) — kontrakty,
których potrzebuje aplikacja; adaptery to konkretne implementacje mieszkające w
infrastrukturze. Aplikacja zależy wyłącznie od protokołów, dzięki czemu nie jest
przywiązana do konkretnych bibliotek (SQLAlchemy, RabbitMQ, Prometheus itd.).

## Problem

Warstwa aplikacji nie może zależeć od szczegółów technicznych (baza, broker,
systemy plików, metryki), bo to uniemożliwia testowanie w izolacji, wymianę
implementacji i utrzymanie reguł architektury (import-linter, mypy). Port
deklaruje *co* aplikacja potrzebuje, a adapter realizuje *jak*.

## Realizacja techniczna

### Porty aplikacji — `shell/platform/application/ports/`

- `ports.py` — port przekrojowy `Logger(Protocol)` z metodami `debug`, `info`,
  `warning`, `error` (sygnatura `msg: str, **kw: object`); re-exportuje
  `Clock`, `DeliveryEnvelope`, `DeliveryTransport`, `EventPublisher`,
  `IdGenerator`, `UnitOfWork` (`__all__`).
- `identity.py` — re-export `IdGenerator` z warstwy domeny
  (`shell/platform/domain/ports/identity.py`): `new_id(id_type: type[TId]) -> TId`
  (`TId` ograniczone do `EntityId`).
- `config.py` — `EventsConfigProtocol` (`outbox_batch_size`, `inbox_batch_size`,
  `worker_poll_interval`, `worker_backoff_factor`, `worker_max_backoff`) oraz
  `AppConfig` (`profile`, `database_url`, `max_step`, `max_parallel`, `log_level`,
  `seed_dev_data`, `reset_db`, `events`).
- `filesystem.py` — `TaskExecutionLoader(Protocol)`: `async load(md_path: str) -> str`.
- `messaging.py` — `EventPublisher` (`async publish(events: Sequence[object])`)
  i `MessagePublisher` (`async publish(messages: Sequence[object])`).
- `metrics.py` — `MetricsBackend(Protocol)` — "pluggable sink" dla metryk
  backlogu inbox; metody `record_backlog(*, pending, processing, processed,
  retry, dead_letter, oldest_pending_age_seconds)`,
  `record_lease_expired(count)`, `record_duplicate_delivery(count)`.
- `readiness.py` — `ReadinessReport` (frozen dataclass `ready: bool`,
  `checks: dict[str, object]`) oraz `ReadinessProbe`: `async check() -> ReadinessReport`.
- `delivery_transport.py` — `DeliveryKind = Literal["event", "message", "command"]`,
  `DeliveryEnvelope` (frozen dataclass: `kind`, `outbox_id`, `contract_type`,
  `occurred_at`, `schema_version`, `payload`, `correlation_id`, `causation_id`) oraz
  `DeliveryTransport`: `async deliver(envelope: DeliveryEnvelope)`.
- `delivery_dedup_store.py` — `DeliveryDedupStore` dla deduplikacji at-least-once
  w handlerach, które **nie mogą** współdzielić transakcji processora:
  `async is_duplicate(outbox_id) -> bool` oraz
  `async mark_processed(outbox_id, *, payload=None, processed_at=None)`.
  Sesję rozwiązuje z aktywnego `DeliverySessionScope`, więc wiersz dedup jest
  pisany w tej samej transakcji co efekt biznesowy; konflikt klucza
  `(consumer_name, outbox_id)` traktowany jako sukces (już przetworzone).
- `unit_of_work.py` — port `UnitOfWork` (patrz [unit-of-work](unit-of-work.md)).

### Adaptery — `shell/platform/infrastructure/`

Adaptery implementują powyższe porty po stronie infrastruktury:

- bazy danych: `persistence/` — m.in. `sql_alchemy_uow_base.py`
  (`SqlAlchemyUnitOfWorkBase` implementuje `UnitOfWork`), modele SQL
  (`sql/models/`), sesje;
- serializacja: `serialization/` — `DomainEventSerializer`, rejestry typów,
  upcaster (`upcaster.py`);
- transport: adaptery `DeliveryTransport` (np. RabbitMQ) — patrz
  [delivery-transport](delivery-transport.md);
- metryki: adaptery `MetricsBackend` konwertujące prymitywy na
  counters/gauges wybranego backendu;
- kontekst (ContextVary): `infrastructure/context/__init__.py` re-exportuje
  `get_correlation_id`, `get_causation_id`, `get_session_scope` i powiązane
  funkcje z `application/context` (patrz [tracing-context](tracing-context.md)).

Porty domenowe (dla warstwy domeny, nie aplikacji) mieszkają w
`shell/platform/domain/ports/` (`identity.py`, `time.py` — `Clock.now()`,
`repository_port.py`, `log.py`).

## Kluczowe pliki

- `shell/platform/application/ports/ports.py`
- `shell/platform/application/ports/identity.py`
- `shell/platform/application/ports/config.py`
- `shell/platform/application/ports/filesystem.py`
- `shell/platform/application/ports/messaging.py`
- `shell/platform/application/ports/metrics.py`
- `shell/platform/application/ports/readiness.py`
- `shell/platform/application/ports/delivery_transport.py`
- `shell/platform/application/ports/delivery_dedup_store.py`
- `shell/platform/application/ports/unit_of_work.py`
- `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py`

## Powiązane koncepcje

- [unit-of-work](unit-of-work.md)
- [domain-ports](domain-ports.md)
- [delivery-transport](delivery-transport.md)
- [metrics](metrics.md)
- [readiness](readiness.md)
- [delivery-dedup] — patrz [processed-delivery-dedup](processed-delivery-dedup.md)
- [architecture-overview](architecture-overview.md)
