---
name: backend-api-standards
description: Standardy API backendu SHELL — tagi OpenAPI, publikacja specyfikacji, wersjonowanie, format odpowiedzi, konwencje endpointów. Reguły dla backendu które frontend konsumuje przez @shell/api-spec.
---

# Backend API Standards

> Backend definiuje API — frontend się dostosowuje. Backend publikuje `openapi.json` jako paczkę npm `@shell/api-spec`, frontend generuje z niej typy i klienta przez Orval.

## 1. OpenAPI Tagi — PascalCase

Każdy endpoint MUSI mieć przypisany tag. Tagi są w PascalCase, odpowiadają Bounded Contextom.

### Obecne tagi

| Tag | Router prefix | Endpointy |
|-----|--------------|-----------|
| `Users` | `/api/v1/users` | GET `/{user_id}`, POST `/`, PUT `/{user_id}`, DELETE `/{user_id}` |
| `Sessions` | `/api/v1/sessions` | GET `/{session_id}/history` |
| `Projects` | `/api/v1/projects` | GET `/{project_id}` (stub 501) |
| `Workflows` | `/api/v1/workflows` | GET `/{workflow_id}` |
| `NodeExecutions` | `/api/v1/node-executions` | GET `/{node_execution_id}/result` |
| `EdgeExecutions` | `/api/v1/edge-executions` | POST `/`, PUT `/{edge_execution_id}`, DELETE `/{edge_execution_id}` |
| `EdgeLinkExecutions` | `/api/v1/edge-links` | POST `/`, DELETE `/{link_id}` |
| `GraphDefinitions` | `/api/v1/graph-definitions` | GET `/{graph_definition_id}`, POST `/by-semantic` |
| `Health` | `/health` | GET `/` |

### Gdzie zmieniać

- **Router tag**: w `shell/framework/<bc>/<aggregate>/api/router.py` — `APIRouter(tags=["TagName"])`
- **OpenAPI metadata**: w `shell/platform/framework/api/openapi.py` — w liście `OPENAPI_TAGS`
- **Health endpoint**: w `shell/platform/framework/api/app.py` — `@app.get("/health", tags=["Health"])`
- **Per-BC app fabryki**: w `shell/framework/**/api/app.py` — `@app.get("/health", tags=["Health"])`

### Zasady dodawania nowego tagu

1. Dodać do `OPENAPI_TAGS` w `openapi.py`
2. Użyć w routerze: `APIRouter(tags=["NewTag"])`
3. Frontend dostosuje `orval.config.ts` po stronie frontendu

## 2. OpenAPI Spec — generowanie i publikacja

Backend publikuje `openapi.json` jako paczkę npm `@shell/api-spec` do GitHub Packages.

### Generowanie lokalne

```bash
python scripts/generate-openapi.py
```

Skrypt importuje aplikację FastAPI i zrzuca specyfikację:

```python
# scripts/generate-openapi.py
import json
from shell.execution.framework.execution.api.app import create_execution_app

app = create_execution_app(...)
with open("openapi.json", "w") as f:
    json.dump(app.openapi(), f, indent=2)
```

### Publikacja przez CI

Plik `.github/workflows/publish-api-spec.yml` — odpala się po `git tag v*`:

1. Generuje `openapi.json`
2. Waliduje JSON
3. Pakuje jako `@shell/api-spec` (npm package)
4. Publikuje do GitHub Packages (`packages: write` permission)

### Endpoint openapi.json w runtime

FastAPI automatycznie serwuje `/openapi.json` — frontend może go pobrać z:

```
GET http://localhost:8000/openapi.json
```

Frontendowy Orval ma to ustawione jako `input.target` w `orval.config.ts`.

## 3. Wersjonowanie API

| Zmiana | Wersja | Przykład |
|--------|--------|----------|
| Breaking change (usunięcie/zmiana pola) | major | `v1.0.0` → `v2.0.0` |
| Nowy endpoint, nowe pole (niełamliwe) | minor | `v1.0.0` → `v1.1.0` |
| Hotfix, dokumentacja | patch | `v1.0.0` → `v1.0.1` |

Wersja jest ustawiona na poziomie gita (`git tag v1.0.0`) → CI publikuje `@shell/api-spec@1.0.0`.

Frontend aktualizuje przez `npm update @shell/api-spec` — nie automatycznie.

## 4. Format odpowiedzi API

### Sukces (200/201)

Endpoint zwraca Pydantic `BaseModel` jako JSON. Każdy model jest w `response_model=` w dekoratorze endpointu.

```python
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str) -> UserResponse:
    ...
```

### Błąd (4xx/5xx)

Backend używa znormalizowanego formatu Problem Detail (RFC 9457):

```json
{
  "type": "about:blank",
  "title": "Not Found",
  "status": 404,
  "detail": "User with id abc-123 not found",
  "instance": "/api/v1/users/abc-123"
}
```

Dla błędów walidacji dodatkowo `errors` z polami:

```json
{
  "title": "Validation Error",
  "status": 422,
  "errors": [
    { "field": "email", "message": "field required" }
  ]
}
```

Nie zmieniaj formatu błędów — frontend ma globalny handler który je parsuje.

### Paginacja

Endpointy listujące używają `Page[T]`:

```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "size": 20,
  "pages": 3
}
```

## 5. Konwencje endpointów

### URL structure

```
/api/v1/{resource}[/{id}][/{sub-resource}]
```

Przykłady:
- `GET /api/v1/users` — lista
- `GET /api/v1/users/{user_id}` — szczegół
- `GET /api/v1/sessions/{session_id}/history` — sub-resource

### HTTP metody

| Metoda | Akcja | Status |
|--------|-------|--------|
| `GET` | Pobierz listę/szczegół | 200 |
| `POST` | Utwórz | 201 |
| `PUT` | Aktualizacja pełna (replace) | 200 lub 204 |
| `PATCH` | Aktualizacja częściowa | 200 |
| `DELETE` | Usuń | 204 |

### ID w URL

ID w ścieżkach URL są zawsze `str` (UUID). Nazwa parametru path: `{resource}_id`.

```python
@router.get("/{user_id}")
async def get_user(user_id: str) -> UserResponse: ...
```

### DTO — tylko str, nie VO

DTO dla frontendu używają typów prostych (`str`, `int`, `datetime | None`). Nigdy Value Object — to warstwa frameworka, nie domeny.

```python
class UserResponse(BaseModel):
    id: str                        # nie UserId
    email: str                     # nie Email
    status: str                    # nie UserStatus
    created_at: datetime | None
```

## 6. Tagi vs przedrostki endpointów

Tagi OpenAPI są niezależne od prefixu URL. Jeden router = jeden tag, ale tag nie musi pokrywać się z path prefixem.

| Reguła | Przykład |
|--------|----------|
| Jeden agregat = jeden router = jeden tag | `EdgeExecutions` → router `/edge-executions` |
| Tag = nazwa agregatu (PascalCase) | `EdgeLinkExecutions` |
| Path = kebab-case | `/edge-links` |

## 7. Dodawanie nowego endpointu — checklista

- [ ] Dodać endpoint w `router.py` z `tags=["ExistingTag"]`
- [ ] Dodać Pydantic `BaseModel` dla request/response (nie importować domenowych VO!)
- [ ] Użyć `response_model=` w dekoratorze
- [ ] Jeśli nowy BC → dodać `OPENAPI_TAGS` w `openapi.py`
- [ ] Jeśli nowy BC → frontend doda wpis w `orval.config.ts`
- [ ] Bumpnąć wersję (git tag) przed publikacją

## 8. Powiązane skille

- [id-naming-convention](../../naming-standards/id-naming-convention/SKILL.md) — konwencja ID: DB `user_id` ↔ domain `UserId` ↔ api `str`
- [mapper-structure](../../pattern-standards/mapper-structure/SKILL.md) — mapowanie między domain VO a DTO
- [shell-architecture](../shell-architecture/SKILL.md) — architektura projektu, warstwy, przepływ
- [dto](../../application-layer/dto/SKILL.md) — DTO jako warstwa kontraktu API
