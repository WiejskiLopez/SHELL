# Principal — kim jest wywołujący (uwierzytelnienie i kontekst użytkownika)

## Cel / Co realizuje

`Principal` (`shell/platform/framework/api/principal.py`) jest jednolitym,
niezmiennym obiektem opisującym wywołującego danego żądania HTTP: identyfikator
podmiotu (`subject_id`) i jego rodzaj (`PrincipalKind.USER` lub
`PrincipalKind.SYSTEM`). Budowany jest raz, w `AuthMiddleware`
(`shell/platform/framework/api/middleware/api_key.py`), zapisywany w
`scope.state["principal"]`, a kontrolery/routera uzyskują go przez zależności
FastAPI `get_principal` / `require_user_principal` / `require_system_principal`.
Testy e2e nadpisują te zależności przez `app.dependency_overrides`.

## Problem

Endpointy muszą wiedzieć, kto wywołuje: zwykły użytkownik (sesja lub JWT) czy
system (API key), oraz muszą móc autoryzować dostęp (np. użytkownik operuje tylko
na własnych zasobach; operacje systemowe tylko dla `SYSTEM`). Decyzja o tożsamości
musi zapaść na granicy HTTP, być wspólna dla wszystkich BC i być reprezentowana
jednolitym typem, żeby kontrolery nie parsowały nagłówków/cookie we własnym
zakresie.

## Realizacja techniczna

### Model — `shell/platform/framework/api/principal.py`

```python
class PrincipalKind(StrEnum):
    USER = "user"
    SYSTEM = "system"

@dataclass(frozen=True, slots=True)
class Principal:
    subject_id: str
    kind: PrincipalKind

SYSTEM_SUBJECT_ID = "system"
```

`Principal` jest frozen dataclass (niezmienny, `__slots__`), `PrincipalKind`
dziedziczy po `StrEnum`.

### Budowa principala — `AuthMiddleware._resolve_principal`

Kolejność (pierwsze trafienie wygrywa):

1. **Sesja** — ciasteczko `shell_session` (`_session_token` przez
   `SimpleCookie`); `query_bus.dispatch(self._session_query_factory(token))`;
   wynik z atrybutem `user_id` → `Principal(session.user_id, PrincipalKind.USER)`.
2. **JWT Bearer** — `Authorization: Bearer <token>`; `_validate_jwt` (HS256,
   `require=["exp", "sub"]`) → `Principal(subject_id, PrincipalKind.USER)`.
3. **API key** — `X-API-Key` równy skonfigurowanemu `api_key`
   → `Principal(SYSTEM_SUBJECT_ID, PrincipalKind.SYSTEM)`.

Sukces zapisuje `scope.setdefault("state", {})["principal"] = principal`;
porażka odpowiada `401` z `ProblemDetail` (title "Unauthorized").

Sekrety (`api_key`, `jwt_secret`) pochodzą z `setup_api_common` (rozwikłane przez
`resolve_api_key` / `resolve_jwt_secret` z `shell/platform/framework/api/setup.py` —
atrybuty kontenera lub `SHELL_API_KEY` / `SHELL_JWT_SECRET` z env).

### Uzyskiwanie principala w kontrolerze

Zależności FastAPI w `shell/platform/framework/api/principal.py`:

- `get_principal(request: Request) -> Principal` — czyta
  `request.state.principal`; gdy brak lub zły typ → `HTTPException(401,
  "Missing or invalid authentication")` (fail-closed).
- `require_user_principal(request)` — `get_principal`, a następnie
  `HTTPException(403, "User authentication required")` gdy
  `kind != PrincipalKind.USER`.
- `require_system_principal(request)` — `HTTPException(403, "System
  authentication required")` gdy `kind != PrincipalKind.SYSTEM`.

Użycie w routerze, np. `shell/session/framework/session/session/api/router.py`:

```python
principal: Principal = Depends(get_principal),
# lub
principal: Principal = Depends(require_user_principal),
```

a w BC user (systemowe operacje), np. `shell/user/framework/user/user/api/router.py`:

```python
principal: Principal = Depends(require_system_principal),
```

Kontrolery wykonują autoryzację na poziomie zasobów na podstawie `Principal`,
np. `UserController._require_access` (`shell/user/framework/user/user/api/controller.py`):
dostęp, gdy `principal.kind == PrincipalKind.SYSTEM` lub
`principal.subject_id == user_id`; w przeciwnym razie `404`.

### Testowalność

- `Principal` porównywalny przez wartości (frozen dataclass), co umożliwia
  asercje w testach (`shell/tests/platform/unit/framework/test_principal.py`,
  `shell/tests/user/integration/platform/test_auth_middleware.py`).
- E2E BC nadpisują zależności:
  `app.dependency_overrides[get_principal] = lambda: TEST_PRINCIPAL`
  (`shell/tests/session/e2e/conftest.py`); helper
  `shell/tests/shared/e2e_helpers.py` ustawia
  `request.state.principal = Principal("test-user", PrincipalKind.USER)`.

## Kluczowe pliki

- `shell/platform/framework/api/principal.py`
- `shell/platform/framework/api/middleware/api_key.py`
- `shell/platform/framework/api/setup.py`
- `shell/user/framework/user/user/api/controller.py`
- `shell/user/framework/user/user/api/router.py`
- `shell/session/framework/session/session/api/router.py`

## Powiązane koncepcje

- [api-middleware](api-middleware.md)
- [http-api](http-api.md)
- [error-handling](error-handling.md)
- [tracing-context](tracing-context.md)
