# Plan dla backendu — publikacja `@shell/api-spec`

## Cel

Backend (FastAPI) publikuje `openapi.json` jako paczkę npm `@shell/api-spec` do GitHub Packages.
Frontend pobiera tę paczkę i generuje z niej typy, klienta Axios i React Query hooki przez Orval.

---

## 1. Struktura backendowego repozytorium (SHELL)

```
(SHELL repo root)
├── .github/
│   └── workflows/
│       └── publish-api-spec.yml    ← CI do publikacji paczki
├── app/
│   └── main.py                     ← FastAPI app
├── requirements.txt
└── scripts/
    └── generate-openapi.py         ← skrypt do generowania openapi.json
```

---

## 2. Otagowanie endpointów (wymagane)

Frontendowy Orval filtruje endpointy po tagach. Każdy endpoint musi mieć przypisany tag.

Wymagane 7 tagów (Bounded Contexty):

| Tag | Przykładowe endpointy |
|---|---|
| `Users` | `GET /api/v1/users`, `POST /api/v1/users`, `GET /api/v1/users/{id}` |
| `Sessions` | `POST /api/v1/sessions`, `DELETE /api/v1/sessions/{id}` |
| `Definitions` | `GET /api/v1/definitions`, `POST /api/v1/definitions` |
| `Executions` | `POST /api/v1/executions`, `GET /api/v1/executions/{id}` |
| `Messaging` | `GET /api/v1/messages`, `POST /api/v1/messages` |
| `Projects` | `GET /api/v1/projects`, `PUT /api/v1/projects/{id}` |
| `Scheduling` | `GET /api/v1/schedules`, `POST /api/v1/schedules` |

Przykład w FastAPI:

```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/users", tags=["Users"])

@router.get("/")
def list_users(): ...

@router.post("/")
def create_user(): ...
```

---

## 3. Skrypt generujący `openapi.json`

### Opcja A — skrypt Python (zalecane)

```python
# scripts/generate-openapi.py
import json
from app.main import app

with open('openapi.json', 'w') as f:
    json.dump(app.openapi(), f, indent=2)
```

Uruchomienie:
```bash
python scripts/generate-openapi.py
```

### Opcja B — curl w CI

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
sleep 3
curl -s -o openapi.json http://localhost:8000/openapi.json
kill %1
```

---

## 4. CI do publikacji

Plik: `.github/workflows/publish-api-spec.yml`

```yaml
name: Publish @shell/api-spec

on:
  push:
    tags:
      - 'v*'  # publikacja tylko po git tag vX.Y.Z

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write    # ← wymagane do GitHub Packages

    steps:
      - uses: actions/checkout@v5

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - run: pip install -r requirements.txt

      - name: Generate OpenAPI spec
        run: python scripts/generate-openapi.py

      - name: Validate OpenAPI spec
        run: python -m json.tool openapi.json > /dev/null

      - name: Extract version from git tag
        run: echo "VERSION=${GITHUB_REF_NAME#v}" >> $GITHUB_ENV

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

      - name: Publish to GitHub Packages
        run: |
          cd dist
          npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Dlaczego `tags: ['v*']`?

- Wersjonowanie przez git tagi
- `git tag v0.1.0` → publikuje `@shell/api-spec@0.1.0`
- `git tag v1.2.3` → publikuje `@shell/api-spec@1.2.3`
- Breaking change = major version (v2.0.0)
- Nowe endpointy (bez breaking change) = minor (v1.1.0)

---

## 5. Konfiguracja GitHub Packages (jednorazowo)

W backendowym repozytorium na GitHubie:

1. **Settings → Actions → General → Workflow permissions**
   - Ustaw: **Read and write permissions**
   - Zaznacz: *Allow GitHub Actions to create and approve pull requests*

2. **Upewnij się że repozytorium jest publiczne**
   - Jeśli prywatne: frontendowe CI będzie potrzebować dodatkowego tokena z dostępem do packages

3. **Nie potrzebujesz dodatkowych secretów**
   - `GITHUB_TOKEN` automatycznie ma dostęp do `packages: write`

---

## 6. Testowanie lokalnie (przed CI)

```bash
# 1. Generujesz spec
python scripts/generate-openapi.py

# 2. Sprawdzasz poprawność JSON
python -m json.tool openapi.json > /dev/null && echo "OK"

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

# 4. Pakujesz lokalnie
cd test-package && npm pack
# → powstanie shell-api-spec-0.1.0.tgz
```

Możesz też przetestować cały pipeline przez ręczne odpalenie workflow na branchu (GitHub Actions → Run workflow → wybrać branch).

---

## 7. Wypuszczenie pierwszej wersji

```bash
git add scripts/generate-openapi.py .github/workflows/publish-api-spec.yml
git commit -m "feat: add OpenAPI spec publishing workflow"
git tag v0.1.0
git push origin main --tags
```

Po pushnięciu taga GitHub Actions uruchomi `publish-api-spec.yml` i opublikuje `@shell/api-spec@0.1.0`.

---

## 8. Co dostaniesz od frontendu po Twojej publikacji

Gdy `@shell/api-spec` pojawi się w GitHub Packages, ja po stronie frontendu:

1. Dodam `@shell/api-spec` do `devDependencies` w `package.json`
2. Skonfiguruję `.npmrc` do GitHub Packages
3. Przekonfiguruję `orval.config.ts` na plik z `node_modules/@shell/api-spec/openapi.json`
4. Uruchomię `npm run generate:api` dla wszystkich 7 feature libs
5. Zmigruję `feature-user` z ręcznego API na generowany kod (wzorzec)
6. Dodam walidację w CI frontendu: `npm run generate:api && git diff --exit-code`

---

## Podsumowanie zadań dla backendu

| # | Zadanie | Kto |
|---|---|---|
| 1 | Dodać tagi OpenAPI do endpointów | Backend team |
| 2 | Stworzyć `scripts/generate-openapi.py` | Backend team |
| 3 | Stworzyć `.github/workflows/publish-api-spec.yml` | Backend team |
| 4 | Ustawić `packages: write` w permissions CI | Backend team |
| 5 | Ustawić `Workflow permissions: Read and write` w GitHub Settings | Backend team |
| 6 | Wypuścić `git tag v0.1.0` | Backend team |
| 7 | Poinformować frontend o pierwszej wersji | Backend team → Frontend |
