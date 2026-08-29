# Metryki dostarczania inbox

## Cel / Co realizuje

Platforma dostarcza minimalny zestaw metryk operacyjnych inbox (backlog, przeterminowane dzierżawy, duplikaty) przez port `MetricsBackend` (`shell/platform/observability/application/ports/metrics.py`) oraz serwis agregujący `InboxMetricsService` (`shell/platform/infrastructure/messaging/inbox/inbox_metrics_service.py`). Dostarczany jest też adapter bez zależności `LoggingMetricsBackend` (`shell/platform/observability/infrastructure/metrics/logging_metrics_backend.py`), który loguje snapshoty do aplikacyjnego loga.

## Problem

Dashboardy i readiness checks potrzebują liczb operacyjnych (ile wiadomości w stanie PENDING, RETRY, DEAD_LETTER itd.), ale platforma nie powinna zależeć od konkretnego backendu metryk (Prometheus i in.). Bez portu każdy BC wiązałby się z konkretną biblioteką i każda zmiana backendu wymuszałaby zmiany w domenie/infrastrukturze dostarczania.

## Realizacja techniczna

### Port `MetricsBackend`

`MetricsBackend` to `Protocol` (`shell/platform/observability/application/ports/metrics.py`) z trzema metodami, wszystkie z argumentami keyword-only:

- `record_backlog(*, pending: int, processing: int, processed: int, retry: int, dead_letter: int, oldest_pending_age_seconds: float | None) -> None` — pełny snapshot backlogu,
- `record_lease_expired(count: int) -> None` — liczba wygasłych dzierżaw,
- `record_duplicate_delivery(count: int) -> None` — liczba zduplikowanych dostaw.

### `InboxMetricsService`

`InboxMetricsService` (konstruktor: `session_factory`, `inbox_model: type[InboxStateModel]`, `backend: MetricsBackend | None = None`) robi dwie kwerendy w `snapshot()`:

1. `select(inbox_model.status, func.count().label("count")).group_by(inbox_model.status)` — liczniki per status,
2. `select(func.min(inbox_model.received_at)).where(status.in_([PENDING.value, RETRY.value]))` — wiek najstarszej wiadomości oczekującej.

Wynik pakuje w `InboxMetrics` — `@dataclass(frozen=True, slots=True)`:

```python
pending: int = 0
processing: int = 0
processed: int = 0
retry: int = 0
dead_letter: int = 0
total: int = 0
oldest_pending_age_seconds: float | None = None
by_status: dict[str, int] = field(default_factory=dict)
```

Pola per-status wypełniane są z `by_status.get(InboxStatus.X.value, 0)`, a `total` to `sum(by_status.values())`. `_age_seconds(oldest)` normalizuje timestamp do `datetime` (isoformat, `tzinfo` uzupełniane do `UTC`) i zwraca `max(age, 0.0)`, albo `None` dla pustego zbioru.

Po zbudowaniu snapshotu `snapshot()` wywołuje `self._emit(metrics)`, które (gdy backend nie jest `None`) woła `backend.record_backlog(...)` w `try/except` — błąd backendu jest logowany (`logger.exception("metrics backend failed to record backlog snapshot")`), ale nie psuje wyniku kwerendy.

### `LoggingMetricsBackend` (adapter bez zależności)

`LoggingMetricsBackend` to `@dataclass(frozen=True, slots=True)` bez jakichkolwiek zależności. Implementuje port przez logowanie:

- `record_backlog` → `logger.info("inbox.backlog pending=%s ... oldest_pending_age_seconds=%s", ...)`,
- `record_lease_expired` → `logger.warning("inbox.lease_expired count=%s", count)`,
- `record_duplicate_delivery` → `logger.warning("inbox.duplicate_delivery count=%s", count)`.

Jest używany do czasu podpięcia realnego backendu (Prometheus itd.) — patrz [ports-and-adapters](ports-and-adapters.md).

### Wiring w kontenerze

Przykładowe podpięcie (BC Ingestion, `shell/ingestion_service/bootstrap/ingestion/container/ingestion_core_container.py`):

```python
inbox_metrics_service = providers.Singleton(
    InboxMetricsService,
    session_factory=session_factory,
    inbox_model=persistence_delivery_models.provided.events.inbox,
    backend=LoggingMetricsBackend(),
)
```

`persistence_delivery_models` to `providers.Object(PERSISTENCE_DELIVERY_MODELS)` (patrz [delivery-models](delivery-models.md)); `inbox_model` wskazuje model inboxa z bundle'a.

## Kluczowe pliki

- `shell/platform/observability/application/ports/metrics.py`
- `shell/platform/infrastructure/messaging/inbox/inbox_metrics_service.py`
- `shell/platform/observability/infrastructure/metrics/logging_metrics_backend.py`
- `shell/platform/domain/value_objects/inbox_status.py`
- `shell/ingestion_service/bootstrap/ingestion/container/ingestion_core_container.py`

## Powiązane koncepcje

- [ports-and-adapters](ports-and-adapters.md)
- [delivery-models](delivery-models.md)
- [inbox-lifecycle](inbox-lifecycle.md)
- [readiness](readiness.md)
- [logging](logging.md)
