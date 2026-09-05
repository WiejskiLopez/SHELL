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

- `logger.py` — port przekrojowy `Logger(Protocol)` z metodami `debug`, `info`,
  `warning`, `error` (sygnatura `msg: str, **kw: object`).
- `config.py` — `EventsConfigProtocol` (`outbox_batch_size`, `inbox_batch_size`,
  `worker_poll_interval`, `worker_backoff_factor`, `worker_max_backoff`) oraz
  `AppConfig` (`profile`, `database_url`, `max_step`, `max_parallel`, `log_level`,
  `seed_dev_data`, `reset_db`, `events`).
- `ports/runtime/filesystem.py` — `TaskExecutionLoader(Protocol)`:
  `async load(md_path: str) -> str`.
- `ports/runtime/seed.py` — `SeedProvider` dla seeding dev danych.
- `ports/messaging/event_publisher.py` — `EventPublisher`
  (`async publish(events: Sequence[object])`).
- `ports/messaging/command_dispatcher.py` — publisher/dyspozytor komend dla
  asynchronicznego command delivery (port `CommandDeliveryDispatcher`).
- `ports/transport/event_transport.py` i `ports/transport/command_transport.py` —
  osobne koperty i porty transportowe: `IntegrationEventDeliveryTransport` z
  `EventDeliveryEnvelope` oraz `CommandDeliveryTransport` z `CommandDeliveryEnvelope`.
- `ports/persistence/unit_of_work.py` — port `UnitOfWork` (patrz
  [unit-of-work](unit-of-work.md)).
- `technical_id_generator.py` — port `TechnicalIdGenerator` (generacja lokalnych
  ID technicznych, np. `inbox.id`).
- `ports/runtime/` zawiera też inne porty runtime'u konsumowane przez infrastrukturę.

Porty obserwowalności żyją w `shell/platform/observability/application/ports/`:
- `metrics.py` — `MetricsBackend(Protocol)` — "pluggable sink" dla metryk backlogu
  inbox/outbox; metody `record_backlog`, `record_outbox_backlog`,
  `record_lease_expired`, `record_duplicate_delivery`;
- `readiness.py` — `ReadinessReport` (frozen dataclass `ready: bool`,
  `checks: dict[str, object]`) oraz `ReadinessProbe`: `async check() -> ReadinessReport`.

Porty domenowe (dla warstwy domeny, nie aplikacji) mieszkają w
`shell/platform/domain/ports/` (`identity.py` — `IdGenerator`, `time.py` — `Clock`,
`repository_port.py`). `Logger` jest portem aplikacji w `application/ports/logger.py`.

### Adaptery — `shell/platform/infrastructure/`

Adaptery implementują powyższe porty po stronie infrastruktury:

- bazy danych: `persistence/` — m.in. `sql_alchemy_uow_base.py`
  (`SqlAlchemyUnitOfWorkBase` implementuje `UnitOfWork`), modele SQL
  (`sql/models/`), sesje, migracje;
- serializacja: `serialization/integration_event/` — `IntegrationEventSerializer`
  / `IntegrationEventDeserializer`, rejestry typów, upcaster (`upcaster.py`);
- transport: adaptery `RabbitEventDeliveryTransport`/`RabbitCommandDeliveryTransport`
  (RabbitMQ) — patrz [delivery-transport](delivery-transport.md);
- metryki: adaptery `MetricsBackend` konwertujące prymitywy na
  counters/gauges wybranego backendu (`observability/infrastructure/metrics/`);
- kontekst (ContextVary): `infrastructure/context/__init__.py` re-exportuje
  `get_correlation_id`, `get_causation_id`, `get_session_scope` i powiązane
  funkcje z `application/context` (patrz [tracing-context](tracing-context.md)).

Idempotencja at-least-once jest realizowana constraintami na tabelach inbox
(`UNIQUE(source_service, event_id|command_id)`) i warunkowym ack — nie wymaga
osobnego portu dedup store.

## Kluczowe pliki

- `shell/platform/application/ports/logger.py`
- `shell/platform/application/ports/config.py`
- `shell/platform/application/ports/runtime/filesystem.py`
- `shell/platform/application/ports/runtime/seed.py`
- `shell/platform/application/ports/messaging/event_publisher.py`
- `shell/platform/application/ports/messaging/command_dispatcher.py`
- `shell/platform/application/ports/transport/event_transport.py`
- `shell/platform/application/ports/transport/command_transport.py`
- `shell/platform/application/ports/persistence/unit_of_work.py`
- `shell/platform/application/ports/technical_id_generator.py`
- `shell/platform/observability/application/ports/metrics.py`
- `shell/platform/observability/application/ports/readiness.py`
- `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py`

## Powiązane koncepcje

- [unit-of-work](unit-of-work.md)
- [domain-ports](domain-ports.md)
- [delivery-transport](delivery-transport.md)
- [metrics](metrics.md)
- [readiness](readiness.md)
- [architecture-overview](architecture-overview.md)