# Backend → Frontend współpraca: wymagania dla backendu

## Cel

Backend (FastAPI) publikuje specyfikację OpenAPI jako paczkę npm `@shell/api-spec` do GitHub Packages. Frontend pobiera tę paczkę i generuje z niej typy, klienta HTTP i React Query hooki — wszystko automatycznie, bez ręcznego klepania kodu API.

---

## 1. Wymagane tagi OpenAPI na endpointach

Frontend filtruje endpointy po tagach (7 Bounded Contextów). Każdy endpoint MUSI mieć przypisany tag:

| Tag | Przykładowe endpointy |
|---|---|
| `Users` | `GET /api/v1/users`, `POST /api/v1/users`, `GET /api/v1/users/{id}`, `PUT /api/v1/users/{id}`, `DELETE /api/v1/users/{id}` |
| `Sessions` | `GET /api/v1/sessions`, `POST /api/v1/sessions`, `GET /api/v1/sessions/{id}`, `PATCH /api/v1/sessions/{id}`, `DELETE /api/v1/sessions/{id}` |
| `Definitions` | `GET /api/v1/definitions`, `POST /api/v1/definitions`, `GET /api/v1/definitions/{id}`, `PUT /api/v1/definitions/{id}`, `DELETE /api/v1/definitions/{id}` |
| `Executions` | `GET /api/v1/executions`, `POST /api/v1/executions`, `GET /api/v1/executions/{id}`, `PATCH /api/v1/executions/{id}`, `DELETE /api/v1/executions/{id}` |
| `Messaging` | `GET /api/v1/messages`, `POST /api/v1/messages`, `GET /api/v1/messages/{id}`, `DELETE /api/v1/messages/{id}` |
| `Projects` | `GET /api/v1/projects`, `POST /api/v1/projects`, `GET /api/v1/projects/{id}`, `PUT /api/v1/projects/{id}`, `DELETE /api/v1/projects/{id}` |
| `Scheduling` | `GET /api/v1/schedules`, `POST /api/v1/schedules`, `GET /api/v1/schedules/{id}`, `PUT /api/v1/schedules/{id}`, `DELETE /api/v1/schedules/{id}` |

Przykład w FastAPI:

```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/users", tags=["Users"])

@router.get("/")
def list_users(): ...

@router.post("/")
def create_user(): ...

@router.get("/{id}")
def get_user(id: str): ...

@router.put("/{id}")
def update_user(id: str): ...

@router.delete("/{id}")
def delete_user(id: str): ...
```

---

## 2. Modele danych (DTO) — oczekiwane przez frontend

Frontend ma już zdefiniowane typy TypeScript. Backendowe DTO powinny być z nimi zgodne:

### User
```python
class UserResponse(BaseModel):
    id: str
    email: str
    status: str          # "active" | "inactive" | "deleted"
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None
```

### Session
```python
class SessionResponse(BaseModel):
    id: str
    goal: str
    status: str          # "completed" | "running" | "pending" | "failed"
    opened_at: datetime | None
    closed_at: datetime | None
```

### Definition (GraphDefinition)
```python
class NodeDefinitionResponse(BaseModel):
    id: str
    node_type: str       # "start" | "process" | "validate" | "end" | ...
    max_step: int | None

class GraphDefinitionResponse(BaseModel):
    id: str
    node_definitions: list[NodeDefinitionResponse]
```

### Execution (Workflow)
```python
class WorkflowResponse(BaseModel):
    workflow_id: str
    status: str          # "completed" | "running" | "pending" | "failed" | "paused"
    session_id: str | None
    created_at: datetime | None
```

### Message
```python
class MessageResponse(BaseModel):
    id: str
    content: str
    type: str            # "info" | "warning" | "error" | "success"
    created_at: datetime
```

### Project
```python
class ProjectResponse(BaseModel):
    id: str
    name: str
    repo_url: str | None
    status: str          # "active" | "draft" | "archived"
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None
```

### Schedule
```python
class ScheduleResponse(BaseModel):
    id: str
    name: str
    cron: str            # wyrażenie cron
    enabled: bool
    created_at: datetime
```

---

## 3. CI/CD — publikacja paczki `@shell/api-spec`

Plik: `.github/workflows/publish-api-spec.yml`

```yaml
name: Publish @shell/api-spec

on:
  push:
    tags:
      - 'v*'  # publikacja po git tag vX.Y.Z

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write    # ← kluczowe: dostęp do GitHub Packages

    steps:
      - uses: actions/checkout@v5

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - run: pip install -r requirements.txt

      # Generowanie openapi.json z FastAPI
      - name: Generate OpenAPI spec
        run: python scripts/generate-openapi.py

      # Walidacja poprawności JSON
      - name: Validate OpenAPI spec
        run: python -m json.tool openapi.json > /dev/null

      # Wyciągnięcie wersji z gita (v1.2.3 → 1.2.3)
      - name: Extract version from git tag
        run: echo "VERSION=${GITHUB_REF_NAME#v}" >> $GITHUB_ENV

      # Przygotowanie paczki npm
      - name: Prepare npm package
        run: |
          mkdir -p dist
          cp openapi.json dist/
          cat > dist/package.json <<EOF
          {
            "name": "@shell/api-spec",
            "version": "${{ env.VERSION }}",
            "description": "OpenAPI specification for SHELL backend",
            "files": ["openapi.json"],
            "license": "MIT"
          }
          EOF

      # Publikacja do GitHub Packages
      - name: Publish to GitHub Packages
        run: |
          cd dist
          npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## 4. Skrypt generujący OpenAPI

Plik: `scripts/generate-openapi.py`

```python
"""Generates openapi.json from the FastAPI application."""
import json
from app.main import app  # dostosuj ścieżkę importu

with open('openapi.json', 'w') as f:
    json.dump(app.openapi(), f, indent=2)

print("✅ openapi.json generated successfully")
```

Uruchomienie lokalne:
```bash
python scripts/generate-openapi.py
```

---

## 5. Wersjonowanie

- **Git tag = wersja paczki**: `git tag v1.0.0` → publikuje `@shell/api-spec@1.0.0`
- **Breaking change** (zmiana istniejących pól, usunięcie endpointu) → major version: `v2.0.0`
- **Nowe endpointy, nowe pola** (niełamliwe) → minor version: `v1.1.0`
- **Hotfixy** → patch version: `v1.0.1`

Frontend decyduje kiedy zaktualizować: `npm update @shell/api-spec`

---

## 6. Konfiguracja GitHub Packages (jednorazowo)

1. **Settings → Actions → General → Workflow permissions**
   - Ustaw: **Read and write permissions**
   - Zaznacz: *Allow GitHub Actions to create and approve pull requests*

2. **Repozytorium backendu powinno być publiczne**
   - Jeśli prywatne — frontendowe CI będzie potrzebować dodatkowego tokena z dostępem do packages

3. **Nie potrzebujesz dodatkowych secretów**
   - `GITHUB_TOKEN` (automatyczny) ma dostęp do `packages: write` przy permissions ustawionych jak wyżej

---

## 7. Testowanie lokalne (przed pierwszym CI)

```bash
# 1. Generujesz spec lokalnie
python scripts/generate-openapi.py

# 2. Sprawdzasz poprawność JSON
python -m json.tool openapi.json

# 3. Symulujesz paczkę npm
mkdir -p test-package
cp openapi.json test-package/
cat > test-package/package.json <<EOF
{
  "name": "@shell/api-spec",
  "version": "0.1.0",
  "files": ["openapi.json"],
  "license": "MIT"
}
EOF

# 4. Pakujesz lokalnie (działa bez Node.js)
cd test-package && npm pack
# → powstanie shell-api-spec-0.1.0.tgz

# 5. Możesz go nawet zainstalować lokalnie w frontendzie:
# cd ../frontend && npm install ../backend/test-package/shell-api-spec-0.1.0.tgz
```

---

## 8. Wypuszczenie pierwszej wersji

```bash
git add scripts/generate-openapi.py .github/workflows/publish-api-spec.yml
git commit -m "feat: add OpenAPI spec publishing workflow"
git tag v0.1.0
git push origin main --tags
```

Po pushnięciu taga:
1. GitHub Actions uruchomi `publish-api-spec.yml`
2. Wygeneruje `openapi.json`
3. Opublikuje `@shell/api-spec@0.1.0` do GitHub Packages

---

## 9. Co dostaje frontend po Twojej publikacji

Gdy paczka pojawi się w GitHub Packages:

1. Frontend dodaje `@shell/api-spec` do `devDependencies`
2. Orval (codegen) generuje typy TypeScript, klienta Axios i React Query hooki
3. Frontend **nie pisze ręcznie żadnego kodu API** — wszystko jest generowane
4. Gdy backend zmieni API → bump wersji → `npm update` → nowy kod → TypeScript pokazuje błędy w miejscach które trzeba poprawić

---

## 10. Podsumowanie checklista dla backendu

- [ ] Otagować endpointy (Users, Sessions, Definitions, Executions, Messaging, Projects, Scheduling)
- [ ] Stworzyć `scripts/generate-openapi.py`
- [ ] Stworzyć `.github/workflows/publish-api-spec.yml`
- [ ] Ustawić `packages: write` w permissions CI
- [ ] Ustawić `Workflow permissions: Read and write` w GitHub Settings
- [ ] Wypuścić `git tag v0.1.0` i pushnąć
- [ ] Powiadomić frontend o pierwszej wersji

---

## 11. Gdy coś nie działa

| Problem | Rozwiązanie |
|---|---|
| `npm publish` w CI fail | Sprawdź czy `packages: write` jest w permissions |
| `openapi.json` pusty | Sprawdź czy FastAPI app importuje się poprawnie |
| Frontend nie widzi paczki | Sprawdź czy `@shell:registry` w `.npmrc` frontendu wskazuje na `https://npm.pkg.github.com` |
| Zmiana w API nie odświeża frontendu | Upewnij się że zmieniłeś wersję (git tag) — frontend nie aktualizuje automatycznie |
