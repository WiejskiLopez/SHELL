# File-Content Naming Consistency — nazwa pliku = główny symbol

## Zasada

Nazwa pliku `.py` MUSI odpowiadać nazwie głównego symbolu (klasy/funkcji),
który definiuje.  Główny symbol to ten, który jest publiczny i re-exportowany
z `__init__.py` lub używany przez inne moduły.

## Przykłady

| Plik | Główny symbol | OK? |
|---|---|---|
| `ingestion.py` | `IngestionModel` | ✅ |
| `message.py` | `IngestionModel` | ❌ — brak `_router` |
| `sql_ingestion_repository.py` | `SqlIngestionRepository` | ✅ |
| `sql_message_repository.py` | `SqlIngestionRepository` | ❌ — brak `_router` |
| `ingestion_entity_to_model.py` | `ingestion_entity_to_model()` | ✅ |
| `message_entity_to_model.py` | `ingestion_entity_to_model()` | ❌ — brak `_router` |

## Konwersja PascalCase → snake_case

Nazwa pliku = `snake_case` wersja nazwy głównej klasy:

| Klasa | Nazwa pliku |
|---|---|
| `IngestionModel` | `ingestion.py` (lub `ingestion_model.py`) |
| `SqlIngestionRepository` | `sql_ingestion_repository.py` |
| `InMemoryIngestionRepository` | `in_memory_ingestion_repository.py` |

Nazwa pliku = dokładna nazwa funkcji (dla mapperów, serwisów):

| Funkcja | Nazwa pliku |
|---|---|
| `ingestion_entity_to_model()` | `ingestion_entity_to_model.py` |
| `ingestion_model_to_entity()` | `ingestion_model_to_entity.py` |

## Wyjątki

1. **`_ensure_utc.py`**, **`_created_at_value.py`** — pliki z funkcją prywatną
   (nazwa z podkreślnikiem) — wyjątek dla helperów w `mappers/`.
2. **`__init__.py`** — stała nazwa, re-exportuje symbole z innych plików.
3. **Pliki w `migrations/versions/`** — nazwa według konwencji Alembic.

## Uzasadnienie

- Konsekwentne nazewnictwo ułatwia nawigację: programista szukający
  `IngestionModel` od razu wie, że plik to `ingestion.py`.
- Eliminuje niejednoznaczność gdy istnieje wiele powiązanych pojęć
  (np. `message` generic vs `ingestion` aggregate).
- Zmniejsza ryzyko konfliktów importów (dwa pliki o nazwie `message.py`
  w różnych pakietach prowadzą do confusion).
