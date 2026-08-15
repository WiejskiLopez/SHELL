# API HTTP (FastAPI) — setup aplikacji, wersjonowanie, OpenAPI, DI

## Cel / Co realizuje

Platforma dostarcza kompletny, wspólny stos HTTP dla aplikacji FastAPI wszystkich
bounded contexts: fabrykę wspólnej konfiguracji aplikacji (`setup_api_common`),
mechanizm wersjonowania API z cyklem życia (`ApiVersionRegistry`, RFC 8594),
generację i publikację specyfikacji OpenAPI oraz wstrzykiwanie zależności
(`ContainerProtocol`, `get_core_container`). Każdy BC tworzy własną aplikację
FastAPI (fabryka `create_*_app`), montuje swoje routery pod prefiksem `/api/v1`
i dołącza wspólne elementy platformy.

## Problem

Bez wspólnej warstwy każdy BC musiałby sam implementować wersjonowanie ścieżek,
nagłówki deprecacji/sunset, rejestrację handlerów błędów, schematy OpenAPI
(`ProblemDetail`, `Page`) i dostęp do kontenera DI w handlerach FastAPI. Powodowałoby
to rozjazd konwencji i duplikację kodu. Wersje API wymagają też jawnego zarządzania
cyklem życia (active → deprecated → sunset), aby klienci mieli czas na migrację.

## Realizacja techniczna

### Tworzenie aplikacji w BC

Każdy BC definiuje fabrykę tworzącą `FastAPI`, np.
`create_execution_app` w `shell/execution/framework/execution/api/app.py`:

```python
app = FastAPI(title="shell — execution", version="0.1.0")
app.state.core_container = core_container
app.add_middleware(CorrelationIdMiddleware)
app.add_exception_handler(DomainError, domain_error_handler)
app.include_router(workflows_router, prefix="/api/v1")
```

- Fabryka ustawia `app.state.core_container` — obiekt kontenera DI widziany przez
  zależności FastAPI.
- Routery BC montowane są pod `prefix="/api/v1"` (prefiks zgodny z
  `API_PREFIX` w `shell/platform/framework/api/constants.py`).
- Liveness `/health` definiowany jest lokalnie w aplikacji BC (zwraca
  `{"status": "ok"}`), a readiness montowany przez `mount_readiness`
  (`shell/platform/framework/api/health.py`) — tylko gdy kontener ma provider
  `readiness_probe`.

### Wspólny setup — `setup_api_common`

`setup_api_common` w `shell/platform/framework/api/setup.py` konfiguruje na raz:

1. `CORSMiddleware` (allow_origins `["*"]`, allow_credentials=True).
2. `CorrelationIdMiddleware`, `AuditLogMiddleware`.
3. `AuthMiddleware` (`shell/platform/framework/api/middleware/api_key.py`)
   z `api_key` i `jwt_secret`.
4. `ApiVersionMiddleware` z przekazanym rejestrem.
5. Handlery błędów (`_register_error_handlers`) i wspólne schematy OpenAPI
   (`_inject_common_schemas`).
6. Endpoint `GET /health` z tagiem `Health`, zwracający:
   `{"status": "ok", "api_version": registry.latest, "latest_version": registry.latest}`.

`create_api_discovery_router` tworzy router z tagiem `ApiDiscovery` i endpointem
`GET /api` zwracającym `{"versions": registry.list_versions(), "latest": registry.latest}`.

Sekrety dla middleware rozwiązywane są przez `resolve_api_key` i `resolve_jwt_secret`
— najpierw z atrybutów kontenera (`container.config.api_key` /
`container.config.jwt_secret`, wspierane jako wartości lub callable), potem z
`os.environ` (`SHELL_API_KEY`, `SHELL_JWT_SECRET`).

### Wersjonowanie API — `version.py`

`shell/platform/framework/api/version.py`:

- `ApiVersionInfo` — frozen dataclass: `version`, `status` (`VersionStatus =
  Literal["active", "deprecated", "sunset"]`), `base_path`,
  `deprecation_date`, `sunset_date`.
- `ApiVersionRegistry` — trzyma wersje w słowniku, `latest` to
  `max(self._versions.keys())`; metody `get_info`, `is_active`,
  `list_versions` (sortowanie malejąco, daty jako ISO string).
- `ApiVersionRegistry.__init__` rzuca `ValueError`, gdy lista jest pusta.

W `shell/platform/framework/api/constants.py` zdefiniowany jest domyślny rejestr:

```python
API_VERSION_REGISTRY = ApiVersionRegistry([
    ApiVersionInfo(version="v1", status="active", base_path="/api/v1"),
])
API_PREFIX = API_VERSION_REGISTRY.get_info("v1").base_path   # "/api/v1"
API_LATEST_VERSION = API_VERSION_REGISTRY.latest             # "v1"
```

### OpenAPI — `openapi.py`

`configure_openapi` w `shell/platform/framework/api/openapi.py` ustawia
`app.title = "SHELL Control Plane API"`, `app.version = "0.1.0"`, opis oraz
`app.openapi_tags = OPENAPI_TAGS` — listę tagów (`Users`, `Sessions`,
`GraphDefinitions`, `Workflows`, `NodeExecutions`, `EdgeExecutions`,
`EdgeLinkExecutions`, `Projects`, `Ingestions`, `SchedulerDefinitions`,
`SchedulerJobs`, `SchedulerExecutions`, `Health`).

`_inject_common_schemas` (w `setup.py`) nadpisuje `app.openapi` customową funkcją,
która po wygenerowaniu schematu przez `get_openapi` dokłada do
`components.schemas` schematy `ProblemDetail`, `Page` i `FieldError`
(przez `model_json_schema()`). Publikacja specyfikacji jest standardowa
(FastAPI wystawia `/openapi.json`, `/docs`, `/redoc`).

### Wstrzykiwanie kontenera — `dependencies.py`

`shell/platform/framework/api/dependencies.py`:

- `ContainerProtocol` — minimalny, neutralny dla platformy kształt kontenera:
  `app`, `infra`, `command_bus`, `query_bus`.
- `get_core_container(request: _Request) -> ContainerProtocol` — czyta
  `request.app.state.core_container`.
- `get_command_bus` / `get_query_bus` — zależności FastAPI z domyślnym
  `Depends(get_core_container)`; przez `_get_buses` obsługują dwa kształty
  kontenera: monolitowy (`container.app.buses.command_bus` /
  `.query_bus`) oraz per-BC (`container.command_bus` / `container.query_bus`).
  Jeśli bus jest callable (brak `dispatch`), jest wywoływany.

Kontrolery BC używają wzorca:
`container: ContainerProtocol = Depends(get_core_container)`, a routery
deklarują fabryki kontrolerów, np. `get_project_controller`
(`shell/project/framework/project/project/api/router.py`).

## Kluczowe pliki

- `shell/platform/framework/api/setup.py`
- `shell/platform/framework/api/version.py`
- `shell/platform/framework/api/constants.py`
- `shell/platform/framework/api/openapi.py`
- `shell/platform/framework/api/dependencies.py`
- `shell/platform/framework/api/health.py`
- `shell/platform/framework/api/readiness.py`
- `shell/execution/framework/execution/api/app.py` (przykład fabryki BC)

## Powiązane koncepcje

- [api-middleware](api-middleware.md)
- [error-handling](error-handling.md)
- [pagination](pagination.md)
- [authentication-principal](authentication-principal.md)
- [readiness](readiness.md)
- [architecture-overview](architecture-overview.md)
