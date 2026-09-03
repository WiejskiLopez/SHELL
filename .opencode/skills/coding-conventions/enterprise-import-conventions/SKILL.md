---
name: enterprise-import-conventions
description: Zero-wyjatkowe zasady importów w enterprise Python. Obejmuje dyscyplinę importów z biblioteki standardowej, higienę __init__.py, strażników TYPE_CHECKING oraz regułę "zawsze importuj z definiującego modułu". Stosuj ślepo, by wyeliminować mypy import-reexport errors i cykliczne zależności.
---

# Konwencje Importów w Enterprise Python (Zero Wyjątków)

## 1. Importy z Biblioteki Standardowej — Zawsze ze Źródła Kanonicznego

Importuj nazwy z biblioteki standardowej bezpośrednio z ich kanonicznego modułu —
bez pośrednictwa podmodułów, re-eksportów ani modułów pośredniczących.

| Nazwa | Import kanoniczny | Przykład błędny (mypy/reexport errors) |
|-------|-------------------|-------------|
| `TYPE_CHECKING` | `from typing import TYPE_CHECKING` | `from moj.pakiet.podmodul import TYPE_CHECKING` |
| `Any` | `from typing import Any` | `from moj.pakiet.podmodul import Any` |
| `Protocol` | `from typing import Protocol` | `from moj.pakiet.podmodul import Protocol` |
| `dataclass` | `from dataclasses import dataclass` | `from moj.pakiet.podmodul import dataclass` |
| `field` | `from dataclasses import field` | `from moj.pakiet.podmodul import field` |
| `datetime` | `from datetime import datetime` | `from moj.pakiet.podmodul import datetime` |
| `annotations` | `from __future__ import annotations` (dyrektywa kompilacji) | `annotations` jako symbol — dyrektywa, nie import |

**Uzasadnienie:** Nazwy z biblioteki standardowej istnieją w dokładnie jednym kanonicznym module. Importowanie ich przez łańcuchy re-eksportu psuje analizę granic modułów w mypy, produkuje fałszywie pozytywne błędy "does not explicitly export attribute" i tworzy kruche sprzężenie do pośredniczących plików `__init__.py`.

## 2. `__init__.py` — Ściśle Ograniczone do API Pakietu

Każdy `__init__.py` MUSI:

1. **Importować tylko nazwy będące częścią publicznego API pakietu.** Użycie wyłącznie wewnętrzne pozostaje lokalne (poza re-eksportem).

2. **Importować nazwy z biblioteki standardowej bezpośrednio z ich kanonicznego źródła.** Przykład:
   ```python
   # DOBRZE
   from dataclasses import dataclass
   from typing import TYPE_CHECKING, Any
   from shell.domain.execution.dto.task_execution import TaskExecutionDto

   __all__ = ["TaskExecutionDto", "dataclass", ...]

   # ŹLE — importuje standardowe nazwy przez podmoduł
   from shell.application.execution.dto.envelope import TYPE_CHECKING, annotations, dataclass
   ```

3. **Zdefiniować jawny `__all__`** zawierający każdą publiczną nazwę. Służy jako dokumentacja ORAZ zaspokaja analizę re-eksportu mypy.

4. **Zadeklarować `from __future__ import annotations`** jako pierwszy import.

5. **Re-eksportować wyłącznie nazwy spoza zasięgu bezpośredniego importu.** Nazwy, które
   konsument importuje bezpośrednio (np. stdlib), pozostają poza `__init__.py` — re-eksport taki
   nie dodaje wartości i psuje analizę mypy.

## 3. Zawsze Importuj z Definiującego Modułu

Importujesz z modułu, który definiuje nazwę; import przez hub re-eksportujący stosujesz
wyłącznie tam, gdzie hub jest granicą publicznego API pakietu, a moduł definiujący
szczegółem implementacyjnym.

```
# ŹLE — importowanie z huba re-eksportującego
from shell.application.platform.ports.identity import IdGenerator

# DOBRZE — importowanie z definiującego modułu
from shell.domain.platform.ports.identity import IdGenerator
```

Wyjątki:
- Adaptery infrastruktury MOGĄ importować z `shell.application.platform.ports.ports` (hub re-eksportujący na poziomie aplikacji), ponieważ moduł portu aplikacyjnego JEST definiującym modułem dla portów warstwy aplikacji.
- `__init__.py` pakietu POWINIEN re-eksportować publiczne typy pakietu dla zewnętrznych konsumentów; zewnętrzni konsumenci POWINNI importować z `__init__.py`.

**Reguła kciuka:** gdy nazwa `X` jest zdefiniowana w module `A`, a inny moduł `B` ją
re-eksportuje, używasz `from A import X`; zapis `from B import X` uzasadnia wyłącznie
granica publicznego API pakietu (`B`) ze szczegółem implementacyjnym (`A`).

## 4. Strażnicy `TYPE_CHECKING` — Spójny Wzorzec

```python
from __future__ import annotations

from typing import TYPE_CHECKING

# Importy runtime'owe na poziomie modułu
from shell.pewien.modul_runtime import KlasaRuntime

if TYPE_CHECKING:
    # Importy tylko-do-typów chronią przed cyklicznymi importami i narzutem runtime'owym
    from shell.pewien.modul_typow import KlasaTylkoTyp
    from datetime import datetime
```

**Zasady:**
- Importy przeznaczone wyłącznie dla adnotacji deklarujesz w bloku `if TYPE_CHECKING:`; importy faktycznie używane w runtime (w tym w `__init__`, `__slots__`, property) deklarujesz poza strażnikiem.
- `from __future__ import annotations` zamienia wszystkie adnotacje na stringi, więc obiekty ze strażnika nie są potrzebne w runtime.

## 5. Każdy Plik MUSI Mieć Kompletne Importy

Gdy dodajesz referencję do typu (np. zmieniasz `dict` na `dict[str, Any]`), MUSISZ zweryfikować, że:

```python
from typing import Any  # ← to jest teraz wymagane
```

Walidację typów wykonuje mypy; `from __future__ import annotations` przenosi ewaluację
adnotacji do narzędzi statycznych (runtime pomija ich analizę). Plik używa typów
`Any`, `Optional`, `Union`, `List`, `Dict`, `Tuple`, `Callable` itd. w pozycji typu —
odpowiedni import `from typing import ...` jest wtedy wymagany.

**Lista kontrolna przy modyfikacji hintów typów w pliku:**
- [ ] Czy używa `Any`? → dodaj `from typing import Any`
- [ ] Czy używa `dict[str, Any]` lub `list[Any]`? → dodaj `from typing import Any` (wbudowane `dict`/`list` są zawsze dostępne)
- [ ] Czy używa `Protocol`? → dodaj `from typing import Protocol`
- [ ] Czy potrzebuje nowego importu w strażniku? → dodaj do bloku `TYPE_CHECKING`

## 6. Zero Niepotrzebnych Re-Eksportów w `__init__.py`

Re-eksport stdlib (`TYPE_CHECKING`, `annotations`, `dataclass`, `field`, `Protocol` itp.)
z `__init__.py` generuje błędy mypy; te nazwy importuje się z kanonicznego źródła.

Jeśli `__init__.py` obecnie to robi, poprawka to:
1. Usuń te nazwy z linii `from podmodul import ...`.
2. Jeśli `__init__.py` potrzebuje tych nazw we własnym `__all__`, zaimportuj je z kanonicznego źródła.
3. Jeśli `__init__.py` NIE potrzebuje ich w `__all__`, usuń je całkowicie.

## 7. Izolacja Warstwy Domenowej

- **Domain** importuje wyłącznie z `shell.domain.*` (oraz stdlib).
- **Application** importuje z `shell.domain.*`.
- **Infrastructure** importuje z `shell.domain.*` oraz `shell.application.*`.

Te kierunki realizują odwrócenie zależności (Dependency Inversion Principle) na poziomie importów.

## 8. Nadpisywanie Mypy w pyproject.toml

Dla modułów, gdzie ścisłe sprawdzanie mypy produkuje nadmiarowe fałszywie pozytywne wyniki (infrastructure, framework, bootstrap, tests), dodaj nadpisanie mypy:

```toml
[[tool.mypy.overrides]]
module = [
    "shell.infrastructure.*",
    "shell.framework.*",
    "shell.bootstrap.*",
    "shell.tests.*",
    "shell.config.*",
]
disallow_untyped_defs = false
disallow_incomplete_defs = false
disallow_untyped_calls = false
disallow_any_generics = false
warn_return_any = false
```

Te moduły nadal korzystają ze ścisłego sprawdzania dla reguł, które mają znaczenie (np. nieużywane ignore, brakujące importy), unikając szumu z wzorców dynamicznych bibliotek.

## 9. Procedura Naprawiania Błędów Importowych

Gdy mypy zgłasza błąd związany z importem:

1. **"Module X does not explicitly export attribute Y"**
   → Sprawdź, czy Y to nazwa z biblioteki standardowej. Jeśli tak, importuj ze źródła kanonicznego (Zasada 1).
   → Sprawdź, czy Y jest zdefiniowane w innym module. Jeśli tak, importuj z definiującego modułu (Zasada 3).
   → W przeciwnym razie dodaj Y do `__all__` modułu źródłowego.

2. **"Name 'Any' is not defined"**
   → Dodaj `from typing import Any` do pliku (Zasada 5).

3. **"import-not-found"**
   → Popraw ścieżkę importu, aby odpowiadała rzeczywistej lokalizacji w systemie plików (Zasada 3, 7).

4. **"Missing type arguments for generic type"**
    → Użyj `dict[str, Any]`, `list[Any]`, `tuple[Any, ...]` zamiast gołych `dict`, `list`, `tuple`.
    → Upewnij się, że `Any` jest zaimportowane (Zasada 5).

## 10. Testowalność Importów — Każdy Import Musi Być Weryfikowalny

Każda instrukcja `from X import Y` w kodzie produkcyjnym musi być testowalna komendą:

```bash
python -c "from X import Y"
```

Jeśli ta komenda failuje z `ModuleNotFoundError` — import wskazuje na nieistniejący moduł i jest **martwym kodem**.

### Kiedy to się zdarza

- Plik został przemianowany (np. `index_document_handler.py` → `document_index_handler.py`) ale importy nie zostały zaktualizowane
- Moduł został usunięty ale referencje w innych plikach pozostały
- Nazwa modułu w imporcie nie zgadza się z rzeczywistą nazwą pliku (np. import `bootstrap_runner_config_handler` ale plik `runner_config_bootstrap_handler.py`)

### Jak weryfikować

Przed commitem sprawdź wszystkie zmienione importy:

```bash
# Dla pliku X, znajdź wszystkie from ... import i przetestuj
python -c "from shell.application.definition.command_handlers.bootstrap_runner_config_handler import RunnerConfigBootstrapHandler"
# → ModuleNotFoundError: No module named '...bootstrap_runner_config_handler'
# → BŁĄD: import wskazuje na nieprawidlowy modul
```

### Automatyzacja

Dodaj skrypt CI który dla każdego pliku `.py` z importami `from shell.` weryfikuje czy importowany moduł istnieje:

```python
# scripts/verify_imports.py
import ast
import sys
from pathlib import Path

def verify_imports(filepath: Path) -> list[str]:
    errors = []
    with open(filepath) as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("shell."):
            parts = node.module.split(".")
            mod_path = Path(*parts)
            if not mod_path.exists() and not (mod_path.with_suffix(".py")).exists():
                errors.append(f"{filepath}: import {node.module} — module not found")
    return errors
```

### Wyjątki

- Importy w bloku `TYPE_CHECKING` dla typów które są używane tylko w adnotacjach — te są leniwie ewaluowane i błąd pojawi się tylko przy rzeczywistym użyciu typu.
- Importy w testach które importują moduły tylko dla typów (nie dla runtime).
