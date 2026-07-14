# File-Content Naming Consistency — nazwa pliku = główny symbol

## Zasada

Nazwa pliku `.py` MUSI odpowiadać nazwie głównego symbolu (klasy/funkcji),
który definiuje.  Główny symbol to ten, który jest publiczny i re-exportowany
z `__init__.py` lub używany przez inne moduły.

## Przykłady

| Plik | Główny symbol | OK? |
|---|---|---|
| `message_router.py` | `MessageRouterModel` | ✅ |
| `message.py` | `MessageRouterModel` | ❌ — brak `_router` |
| `sql_message_router_repository.py` | `SqlMessageRouterRepository` | ✅ |
| `sql_message_repository.py` | `SqlMessageRouterRepository` | ❌ — brak `_router` |
| `message_router_entity_to_model.py` | `message_router_entity_to_model()` | ✅ |
| `message_entity_to_model.py` | `message_router_entity_to_model()` | ❌ — brak `_router` |

## Konwersja PascalCase → snake_case

Nazwa pliku = `snake_case` wersja nazwy głównej klasy:

| Klasa | Nazwa pliku |
|---|---|
| `MessageRouterModel` | `message_router.py` (lub `message_router_model.py`) |
| `SqlMessageRouterRepository` | `sql_message_router_repository.py` |
| `InMemoryMessageRouterRepository` | `in_memory_message_router_repository.py` |

Nazwa pliku = dokładna nazwa funkcji (dla mapperów, serwisów):

| Funkcja | Nazwa pliku |
|---|---|
| `message_router_entity_to_model()` | `message_router_entity_to_model.py` |
| `message_router_model_to_entity()` | `message_router_model_to_entity.py` |

## Wyjątki

1. **`_ensure_utc.py`**, **`_created_at_value.py`** — pliki z funkcją prywatną
   (nazwa z podkreślnikiem) — wyjątek dla helperów w `mappers/`.
2. **`__init__.py`** — stała nazwa, re-exportuje symbole z innych plików.
3. **Pliki w `migrations/versions/`** — nazwa według konwencji Alembic.

## Uzasadnienie

- Konsekwentne nazewnictwo ułatwia nawigację: programista szukający
  `MessageRouterModel` od razu wie, że plik to `message_router.py`.
- Eliminuje niejednoznaczność gdy istnieje wiele powiązanych pojęć
  (np. `message` generic vs `message_router` aggregate).
- Zmniejsza ryzyko konfliktów importów (dwa pliki o nazwie `message.py`
  w różnych pakietach prowadzą do confusion).
