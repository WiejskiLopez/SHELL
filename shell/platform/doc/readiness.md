# Readiness (gotowość serwisu)

## Cel / Co realizuje

Port `ReadinessProbe` (`shell/platform/observability/application/ports/readiness.py`) oraz jego implementacja `SqlReadinessProbe` (`shell/platform/observability/infrastructure/health/sql_readiness_probe.py`) odpowiadają na pytanie "czy ten proces może teraz wykonać użyteczną pracę". Endpoint `GET /readiness` (`shell/platform/observability/framework/api/readiness.py`) zwraca `503` z diagnostycznym ciałem, dopóki serwis nie jest gotowy. `mount_readiness` (`shell/platform/observability/framework/api/health.py`) montuje ten endpoint w aplikacji BC tylko wtedy, gdy kontener rejestruje probe.

## Problem

`/health` odpowiada tylko na pytanie o liveness (proces żyje). W systemie z delivery (inbox/outbox) proces może żyć, ale nie być w stanie wykonać pracy: baza nieosiągalna, migracje (baseline) nieuruchomione, worker martwy przy narastającym backlogu. Orkiestracja (np. Kubernetes) potrzebuje osobnego sygnału ready, opartego o realny stan infrastruktury i przepływu, a nie o sam fakt działania procesu.

## Realizacja techniczna

### Port i raport

```python
@dataclass(frozen=True, slots=True)
class ReadinessReport:
    ready: bool
    checks: dict[str, object] = field(default_factory=dict)

class ReadinessProbe(Protocol):
    async def check(self) -> ReadinessReport: ...
```

`ReadinessReport` niesie flagę `ready` oraz mapę `checks` (nazwa sprawdzenia → wynik), którą endpoint zwraca jako ciało odpowiedzi.

### `SqlReadinessProbe`

Konstruktor: `session_factory`, `inbox_model: type[InboxStateModel]`, `max_backlog: int = 1000`, `worker_heartbeat_model: type[_WorkerHeartbeatReadModel] | None = None`, `worker_stale_after_seconds: float = 30.0`.

`check()` wykonuje kolejno cztery sprawdzenia w jednej sesji:

- `database` — realny round-trip: `await session.execute(text("SELECT 1"))`,
- `migrations` — `select(func.count()).select_from(self._inbox_model)`; tabela istnieje tylko po uruchomieniu baseline (patrz [delivery-models](delivery-models.md)); błąd → `False`,
- `worker` — liveness workera (szczegóły niżej),
- `backlog` — `count(status IN (PENDING, RETRY)) <= max_backlog`.

Żadne sprawdzenie nie rzuca wyjątkiem: całość jest owinięta w `try/except Exception`, a w razie błędu `checks["database"]` dostaje `f"error: {type(exc).__name__}: {exc}"`, a pozostałe — `"not checked"`. `ready` to `all(isinstance(value, bool) and value is True for value in checks.values())`, więc endpoint może odpowiedzieć `503` z treścią diagnostyczną zamiast 500.

### Sprawdzenie `worker`

`_check_worker` rozstrzyga liveness w dwóch trybach:

1. Gdy `worker_heartbeat_model` jest skonfigurowany (rekomendowane): liczy wiersze `last_seen_at > now - timedelta(seconds=worker_stale_after_seconds)`; świeży heartbeat → worker żyje.
2. Fallback na dzierżawy: liczy wiersze `status == PROCESSING AND lease_until > now` (aktywny posiadacz dzierżawy).

Jeśli żaden tryb nie potwierdzi żywego workera, sprawdzenie przechodzi tylko wtedy, gdy backlog jest pusty (`count(PENDING, RETRY) == 0`) — serwis idle, ale zdrowy jest ready. `now` pochodzi z bazy przez `_database_now` (`select(func.current_timestamp())` z normalizacją `tzinfo` do `UTC`), więc porównania nie zależą od zegara procesu.

### Endpoint `/readiness`

`create_readiness_router(probe: ReadinessProbe) -> APIRouter` (`shell/platform/observability/framework/api/readiness.py`) definiuje `GET /readiness`:

```python
report = await probe.check()
payload = {"status": "ready" if report.ready else "not_ready", "checks": report.checks}
if not report.ready:
    response.status_code = 503
return payload
```

Router ma `tags=["Health"]`. Liveness pozostaje w `GET /health` definiowanym przez każdy BC.

### Montowanie w BC

`mount_readiness(app: FastAPI, core_container: ContainerProtocol | Any)` (`shell/platform/observability/framework/api/health.py`) odpytuje kontener o atrybut `readiness_probe` przez `getattr` i montuje router tylko, gdy jest zarejestrowany — BC bez workerów delivery zostają liveness-only.

Rejestracja w kontenerze (np. `shell/ingestion_service/bootstrap/ingestion/container/ingestion_core_container.py`):

```python
readiness_probe = providers.Singleton(
    SqlReadinessProbe,
    session_factory=session_factory,
    inbox_model=persistence_delivery_models.provided.events.inbox,
    max_backlog=1000,
    worker_heartbeat_model=persistence_delivery_models.provided.worker_heartbeat,
)
```

Analogiczne rejestracje istnieją w kontenerach BC: `definition`, `project`, `session`, `scheduling`, `execution`, `user`.

## Kluczowe pliki

- `shell/platform/observability/application/ports/readiness.py`
- `shell/platform/observability/infrastructure/health/sql_readiness_probe.py`
- `shell/platform/observability/framework/api/readiness.py`
- `shell/platform/observability/framework/api/health.py`
- `shell/platform/domain/value_objects/inbox_status.py`
- `shell/ingestion_service/bootstrap/ingestion/container/ingestion_core_container.py`
- `shell/tests/platform/integration/sql_sqlite/test_readiness_probe.py`

## Powiązane koncepcje

- [http-api](http-api.md)
- [delivery-models](delivery-models.md)
- [heartbeat-lease](heartbeat-lease.md)
- [metrics](metrics.md)
- [polling-worker](polling-worker.md)
