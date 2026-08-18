# Middleware API — correlation_id, autoryzacja, wersja, audyt

## Cel / Co realizuje

Warstwa middleware HTTP platformy obsługuje przekrojowe aspekty każdego żądania:
propagację `correlation_id` (`CorrelationIdMiddleware`), uwierzytelnienie i budowę
`Principal` (`AuthMiddleware`), negocjację wersji API z nagłówkami RFC 8594
(`ApiVersionMiddleware`) oraz logowanie audytu (`AuditLogMiddleware`). Middleware
działają na poziomie ASGI (scope), więc są niezależne od warstwy FastAPI.

## Problem

Rozproszone żądania wymagają spójnej korelacji logów (każdy log audytu musi
nosić `correlation_id`). Każdy chroniony endpoint potrzebuje decyzji "kto
wywołuje" (klucz API, JWT, sesja) zanim trafi do kontrolera. Wersjonowanie API
musi być rozwiązywane na granicy HTTP (ścieżka lub nagłówek) i sygnalizować
klientom deprecację. Bez centralnych middleware każdy BC powielałby te mechanizmy
i rozjeżdżałby się w szczegółach.

## Realizacja techniczna

### Kolejność i rejestracja

W `setup_api_common` (`shell/platform/framework/api/setup.py`) middleware
rejestrowane są w kolejności:

```python
app.add_middleware(CORSMiddleware, ...)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(AuditLogMiddleware)
app.add_middleware(AuthMiddleware, api_key=api_key, jwt_secret=jwt_secret)
app.add_middleware(ApiVersionMiddleware, registry=registry)
```

Ze względu na sposób budowania stosu przez Starlette (ostatnio dodany middleware
jest najbardziej zewnętrzny), `ApiVersionMiddleware` i `AuthMiddleware` działają
przed logowaniem audytu i ustawieniem `correlation_id`. Poszczególne BC mogą też
montować middleware samodzielnie, np. `create_execution_app` dodaje
`CorrelationIdMiddleware` i handler `DomainError`.

### CorrelationIdMiddleware — `shell/platform/framework/api/middleware/correlation_id.py`

- Dla scope `type != "http"` przepuszcza żądanie bez zmian.
- Czyta nagłówek `X-Correlation-ID` (`x-correlation-id`) z scope; jeśli obecny,
  ustawia go w ContextVar przez `set_correlation_id(cid)`
  (`shell/platform/application/context/correlation_id.py`).
- W odpowiedzi (`http.response.start`) dokłada nagłówek `X-Correlation-ID`
  tylko, gdy cid był obecny w żądaniu (bramki generują swój identyfikator po stronie
  wejściowej).
- W `finally` resetuje ContextVar przez `reset_correlation_id(token)`, więc
  każdy request ma izolowany kontekst (bez wycieków między requestami).

### AuthMiddleware — `shell/platform/framework/api/middleware/api_key.py`

- Polityka ścieżek publicznych jest przekazywana do konstruktora jako
  niemutowalne `public_exact` i `public_prefix`. Brak konfiguracji oznacza
  fail-closed; wyjątki publiczne należą do właściwego service factory.
- Dla pozostałych ścieżek `_resolve_principal` próbuje kolejno:
  1. **Sesja** — ciasteczko `shell_session` (`_session_token` przez `SimpleCookie`);
     zapytanie o sesję przez `query_bus.dispatch(session_query_factory(token))`
     (factory wstrzykiwana z zewnątrz); jeśli wynik ma `user_id` →
     `Principal(session.user_id, PrincipalKind.USER)`.
  2. **JWT Bearer** — nagłówek `Authorization: Bearer <token>`; `_validate_jwt`
     dekoduje HS256 z `require=["exp", "sub"]` i zwraca `sub` jako `subject_id`
     (`PrincipalKind.USER`).
  3. **API key** — nagłówek `X-API-Key`, porównanie z `self._api_key`;
     sukces → `Principal(SYSTEM_SUBJECT_ID, PrincipalKind.SYSTEM)`.
- Brak principala → odpowiedź `401` z `ProblemDetail` (title
  "Unauthorized", `correlation_id` z `get_correlation_id()`).
- Sukces → `scope.setdefault("state", {})["principal"] = principal` — to jest
  jedyne źródło principala dla `get_principal`.

### ApiVersionMiddleware — `shell/platform/framework/api/middleware/api_version.py`

- Rozwiązywanie wersji (`_resolve_version`) wg priorytetu:
  1. **URL path**: `API_PATH_PATTERN = re.compile(r"^/api/([^/]+)")` — jeśli
     segment istnieje w rejestrze.
  2. **Header**: `X-API-Version` — jeśli wartość istnieje w rejestrze.
  3. **Fallback**: `registry.latest`.
- Wynik zapisywany w `scope.state["api_version"]`.
- W odpowiedzi dokłada nagłówki:
  - `X-API-Version: {resolved_version}` (zawsze);
  - `Deprecation` (RFC 8594) — gdy `status == "deprecated"` i jest
    `deprecation_date`;
  - `Sunset` — gdy `status == "sunset"` i jest `sunset_date`.

### AuditLogMiddleware — `shell/platform/framework/api/middleware/audit_log.py`

- Mierzy czas `perf_counter`, przechwytuje status odpowiedzi przez
  `send_wrapper` (domyślne `500` gdy odpowiedź nie nadeszła).
- Loguje przez `logging.getLogger("shell.api.audit")` rekord `"audit"` z
  `extra`: `method`, `path`, `query_string`, `status`, `elapsed_ms`,
  `correlation_id` (z `get_correlation_id()`), `user_agent`
  (przez `_get_header(scope, "user-agent")`).
- Konfiguracja formattera/JSON należy do infrastruktury logowania (por.
  `shell/platform/infrastructure/logging/`).

## Kluczowe pliki

- `shell/platform/framework/api/middleware/correlation_id.py`
- `shell/platform/framework/api/middleware/api_key.py`
- `shell/platform/framework/api/middleware/api_version.py`
- `shell/platform/framework/api/middleware/audit_log.py`
- `shell/platform/application/context/correlation_id.py`

## Powiązane koncepcje

- [http-api](http-api.md)
- [authentication-principal](authentication-principal.md)
- [error-handling](error-handling.md)
- [tracing-context](tracing-context.md)
- [logging](logging.md)
