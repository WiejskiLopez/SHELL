# Przepływ komendy w SHELL — DROGA SYNCHRONICZNA

Status: analiza stanu faktycznego kodu
Data: 2026-09-01
Zakres: komenda lokalna wykonywana w jednym Bounded Context (write side), bez przekraczania granicy BC.

---

## 0. Charakterystyka

- **Tryb**: `HTTP → Controller → CommandBus → Handler → UnitOfWork → Aggregate → commit` — komenda jako **obiekt w pamięci**, odpowiedź wraca bezpośrednio do caller'a.
- **Transakcja**: jedna, lokalna, własna sesja UoW handlera (brak session scope).
- **Zasięg**: ten sam proces/BC. Komenda **nie jest persistowana**.
- **Gwarancja**: synchronous request/response. Awaria → wyjątek do API, brak trwałego stanu.

```mermaid
flowchart TD
    C[Klient / Frontend / CLI] -->|POST /api/v1/projects X-Correlation-ID X-API-Key| M1[CorrelationIdMiddleware]
    M1 --> A[AuthMiddleware - X-API-Key]
    A --> R[router.py - FastAPI APIRouter]
    R -->|Depends get_core_container| CT[ProjectController]
    CT --> CB[CommandBus.dispatch CreateProjectCommand]
    CB -->|factory()| H[CreateProjectHandler]
    H --> U[SqlAlchemyProjectUnitOfWork]
    U -->|save| REPO[SqlProjectRepository]
    REPO --> AGG[Project.create]
    AGG -->|append_event| EV[ProjectCreatedEvent]
    U -->|commit| OUT[outbox_event + audit_event]
    AGG -->|ProjectId| H
    H --> CT
    CT -->|CreateProjectResponse 201| C
```

---

## 1. Przepływ krok po kroku

Przykład: `POST /api/v1/projects/` w `project_service`.

| # | Krok | Gdzie (plik:linia) | Co się dzieje |
|---|---|---|---|
| 1 | Request HTTP | `shell/project_service/framework/project/project/api/app.py:29` (`create_project_app`), middleware `:37-44` | `CorrelationIdMiddleware` ustawia `correlation_id` z nagłówka (`shell/platform/framework/api/middleware/correlation_id.py:16-39`), `AuthMiddleware` weryfikuje API key. |
| 2 | Routing | `shell/project_service/framework/project/project/api/router.py:28` (APIRouter), `:60-65` (`POST "/"`) | Endpoint wstrzykuje `ProjectController` przez `Depends(get_project_controller)` (`router.py:31-40`), który pobiera `CommandBus` z kontenera. |
| 3 | Controller | `shell/project_service/framework/project/project/api/controller.py:96-100` | `await self._command_bus.dispatch(CreateProjectCommand(name=..., repo_url=...))`. Kontroler nie zawiera logiki biznesowej. |
| 4 | CommandBus | `shell/platform/application/bus/command_bus.py:9-21` | `register(command_type, factory)` zapisuje fabrykę handlera; `dispatch(command)` → `factory()` → `await handler.handle(command)`. Słownik `dict[type, Callable]`. |
| 5 | Rejestracja | `shell/project_service/bootstrap/project/container/project_core_container.py:215-238` | `configure_project_container` rejestruje `CreateProjectCommand → create_project_handler_factory` (:236). Każda komenda musi mieć handler. |
| 6 | Command DTO | `shell/project_service/application/project/project/commands/create_project_command.py:6-13` | `@dataclass(frozen=True, slots=True)`, walidacja strukturalna w `__post_init__`. |
| 7 | Handler | `shell/project_service/application/project/project/command_handlers/create_project_handler.py:27-45` | Generuje `ProjectId`, buduje VO, `Project.create(...)`, `async with unit_of_work: await unit_of_work.save(ProjectRepository, project)`. Zwraca `project_id`. |
| 8 | UnitOfWork (wejście) | `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py:117-129` | `__aenter__`: w ścieżce synchronicznej session scope jest `None`, więc tworzy **własną sesję** (`_deferred_commit = False`). |
| 9 | save + pull_events | `sql_alchemy_uow_base.py:111-115` | `repository(repo_type)` tworzy `SqlProjectRepository(self._active_session)` (`shell/project_service/infrastructure/project/project/persistence/sql/unit_of_work.py:25-35`), zapisuje agregat, potem `aggregate.pull_events()` (`shell/platform/domain/base/aggregate_root.py:37-40`) i `stage_events(...)`. |
| 10 | Agregat | `shell/project_service/domain/project/aggregates/project/project.py:115-125` (`Project.create`), `:109-111` (`append_event ProjectCreatedEvent`) | Mutacja stanu + nagranie zdarzenia domenowego do bufora `AggregateRoot._events` (`aggregate_root.py:27-35`). |
| 11 | commit | `sql_alchemy_uow_base.py:142-157` | `_write_staged_outbox()` (:159-190) w **tej samej transakcji**: mapuje event (`ReflectiveIntegrationMapper` → `IntegrationEvent`), `IntegrationEventSerializer().to_envelope(...)`, `session.add(outbox_event)` + `session.add(audit_event)`. Potem `session.commit()`. Efekt atomowy: **stan agregatu + outbox + audit**. |
| 12 | Odpowiedź | `controller.py:100` → `app.py` | Zwraca `CreateProjectResponse(id=...)` ze statusem 201. Błąd domenowy → `domain_error_handler` (`app.py:45`). |

---

## 2. Granice odpowiedzialności (warstwy)

- **Framework** — `router.py`, `controller.py`, request/response DTO, middleware. Tylko przekazanie.
- **Application** — `CreateProjectCommand` (DTO), `CreateProjectHandler` (koordynacja UoW, VO, porty). Zero logiki biznesowej w handlerze.
- **Domain** — `Project` (agregat), `ProjectCreatedEvent`, VO, `ProjectRepository` (port). Guard-y i invarianty.
- **Infrastructure** — `SqlAlchemyProjectUnitOfWork`, `SqlProjectRepository`, `PERSISTENCE_DELIVERY_MODELS`, sesja, serializacja outboxa.
- **Bootstrap** — `ProjectCoreContainer` + `configure_project_container` (rejestracja handlerów do busów), `main.py` (composition root).

---

## 3. Transakcyjność — czy zgubimy komendę?

### 3.1 Co jest atomowe

| Ogniwo | Mechanizm | Utrata? |
|---|---|---|
| Mutacja + outbox + audit | jedna transakcja `sql_alchemy_uow_base.py:142-190` | ❌ nie atomowo — crash przed commitem → rollback → spójnie (brak efektu i brak outboxa). |
| Błąd serializacji eventu | wyjątek w `_write_staged_outbox` / mapperze | ❌ nie — wyjątek propaguje → commit się nie wykonuje → API zwraca błąd. |
| StaleDataError (wersjonowanie optymistyczne) | `sql_alchemy_uow_base.py:155-157` → `ConcurrentModificationError` | ❌ nie — transakcja wycofana, brak cząstkowego stanu. |

### 3.2 Realne luki ścieżki synchronicznej

| # | Ryzyko | Szczegóły | Rekomendacja |
|---|---|---|---|
| 1 | **Brak idempotencji na API** | `POST /projects` nie ma `Idempotency-Key` (`router.py:60-65`). Crash po commicie, a przed wysłaniem odpowiedzi (lub zwykła retry klienta) → caller widzi błąd i ponawia → **duplikat efektu** (np. drugi projekt). `CreateProjectCommand` nie niesie żadnego stabilnego id. | Wprowadzić `Idempotency-Key` → dedup po kluczu (np. tabela/redis + unique). |
| 2 | Komenda nie jest persistowana | crash w trakcie handlera → komenda znika, efekt nie | ✅ akceptowalne dla semantyki sync HTTP (klient ponawia). Jeżeli operacja ma być odtwarzalna, przenieść na ścieżkę asynchroniczną (outbox). |
| 3 | Brak limitu kontekstu sesji | handler trzyma sesję tylko przez `async with`; długie przetwarzanie → timeout/połączenie | ✅ nie utrata; kwestia operacyjna (timeouty, pool size). |
| 4 | Błąd cross-encji | brak obsługi wielu agregatów w jednym UoW poza repo mapą BC | ⚠️ jeśli logika wymaga 2 agregatów w 1 transakcji, patrz domain-service + wzorzec w `unit-of-work.md`. |

### 3.3 Ocena ogólna

Ścieżka synchroniczna **nie gubi komendy** w sensie atomowości — jest albo cały efekt, albo nic. Jedynym realnym problemem jest **brak deduplikacji po stronie wejścia HTTP** (duplikaty przy retry), nie utrata. Klient nie ma gwarancji exactly-once.

---

## 4. Kluczowe pliki

- `shell/project_service/framework/project/project/api/{app,router,controller}.py`
- `shell/project_service/application/project/project/commands/create_project_command.py`
- `shell/project_service/application/project/project/command_handlers/create_project_handler.py`
- `shell/project_service/domain/project/aggregates/project/project.py`
- `shell/platform/domain/base/aggregate_root.py`
- `shell/platform/application/bus/command_bus.py`
- `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py`
- `shell/project_service/infrastructure/project/project/persistence/sql/unit_of_work.py`
- `shell/project_service/bootstrap/project/container/project_core_container.py`
- `shell/project_service/bootstrap/project/main.py`
