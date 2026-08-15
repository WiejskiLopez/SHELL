# SHELL Architecture — Infrastructure Directory Structure

## Topologia platformy, BC i testów

- `shell/platform/` zawiera wyłącznie generyczne prymitywy i kontrakty; nie importuje BC.
- Kod konkretnego bounded contextu należy do `shell/<bc>/domain`, `application`,
  `process`, `infrastructure`, `framework` lub `bootstrap`.
- Nie ma wspólnego trybu monolitycznego ani wspólnego composition root.
- `shell/tests/platform/` testuje tylko `shell.platform` i nie importuje BC.
- `shell/tests/<bc>/` testuje jeden BC i może importować tylko własny BC oraz platformę.
- `shell/tests/contracts/` testuje publiczne kontrakty HTTP/event między BC.
- `shell/tests/system/` testuje kilka osobnych aplikacji BC, bez wspólnego kontenera.
- `shell/tests/architecture/` zawiera centralne testy AST/importów całego repozytorium.
- `shell/tests/shared/` zawiera tylko helpery generyczne.

Jeśli test platformy importuje BC, zgeneryzuj go na fake platformowy albo przenieś
do testów właściwego BC. Test architektoniczny pozostaje w `shell/tests/architecture/`.

## Obowiązująca struktura katalogów

Każdy agregat w `shell/<bounded_context>/infrastructure/<bounded_context>/<aggregate>/` MUSI stosować:

```
<aggregate>/
  __init__.py                          (opcjonalny — jeśli agregat ma publiczny interfejs)
  persistence/
    sql/
      mappers/                         (1 funkcja = 1 plik, nazwa pliku = nazwa funkcji)
      models/                          (modele SQLAlchemy)
      repositories/                    (implementacje repozytoriów SQL)
      services/                        (query services, read models)
      unit_of_work.py                  (opcjonalnie — Unit of Work SQL)
    memory/
      in_memory_<aggregate>_repository.py
  http/                                (opcjonalnie — adaptery HTTP)
  filesystem/                          (opcjonalnie — adaptery systemu plików)```

### Zasady

1. **Persistence zawsze pod `persistence/`** — nigdy bezpośrednio `sql/` lub `memory/` w katalogu agregatu.
2. **`sql/` adapter** — implementacje portów repozytorium, modele ORM, mappery, serwisy zapytań.
3. **`memory/` adapter** — in-memory implementacje portów repozytorium (używane w testach).
4. **Mappers ZAWSZE jako katalog `mappers/`** — nigdy jako plik `mappers.py`. Każda funkcja mapper w osobnym pliku `.py` nazwanym jak funkcja. `__init__.py` zawiera tylko re-exporty (lub jest pusty).
5. **Adapters poza `persistence/`** — adaptery do zewnętrznych systemów (HTTP, filesystem) mają własny katalog na poziomie agregatu, obok `persistence/`.
6. **Brak pustych katalogów** — nie pozostawiaj pustych `persistence/` na poziomie BC; persistence należy do agregatu.

### Uwagi szczególne

- **`ingestion/`** — BC przyjmujący i normalizujący komunikację wejściową; techniczne mechanizmy event/message/command pozostają w `shell/platform/infrastructure/messaging/`.
- **`scheduler_job/`** — agregat istnieje tylko w domenie (`shell/scheduling/domain/scheduling/aggregates/scheduler_job/`); brak implementacji w infrastrukturze.

### Struktura dla bounded context

```
shell/<bounded_context>/infrastructure/<bounded_context>/
  <aggregate_1>/            ← każdy agregat z własnym persistence/
  <aggregate_2>/
  services/                 (opcjonalnie — serwisy współdzielone na poziomie BC)
  ...
```

### Mappers — szczegółowo

```
mappers/
  __init__.py                        (re-exporty lub pusty; NIGDY funkcji)
  user_model_to_entity.py            (1 funkcja = 1 plik)
  user_entity_to_model.py
  user_update_model.py
```

Każda funkcja mapper — osobny plik `.py`, nazwa pliku = nazwa funkcji.
`__init__.py` tylko importuje i re-eksportuje:

```python
# __init__.py — tylko re-exporty
from .user_model_to_entity import user_model_to_entity
from .user_entity_to_model import user_entity_to_model
from .user_update_model import user_update_model
```

Funkcje prywatne (`_ensure_utc`, `_created_at_value`) też we własnych plikach — nie ma wyjątku dla helperów.

### Wzorzec importów

```python
# DOBRZE — przez __init__.py (re-export)
from shell.<bc>.infrastructure.<bc>.<aggregate>.persistence.sql.mappers import user_model_to_entity

# DOBRZE — bezpośrednio z pliku funkcji
from shell.<bc>.infrastructure.<bc>.<aggregate>.persistence.sql.mappers.user_model_to_entity import (
    user_model_to_entity,
)

# ŹLE — mappers.py jako plik
from shell.infrastructure.<bc>.<aggregate>.persistence.sql.mappers import ...  # ZAKAZANE

# ŹLE — bezpośrednio sql/
from shell.infrastructure.<bc>.<aggregate>.sql.<some_adapter> import ...  # ZAKAZANE
```
