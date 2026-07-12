# Import Organization — Zero-Wyjatkowe Reguły

## 1. Zawsze Importuj z Definiującego Modułu

Każda nazwa ma dokładnie jeden moduł, w którym jest *zdefiniowana*. Importuj zawsze stamtąd, nigdy z `__init__.py` ani innego re-eksportu.

```python
# ŹLE — import z re-eksportującego __init__.py
from shell.domain.execution import TaskExecutionDto
from shell.domain.execution.dto.task_execution import TaskExecutionDto, TaskExecutionStatus

# ŹLE — import stdlib przez projektowy __init__.py
from shell.domain.execution import dataclass, field

# DOBRZE — import z definiującego modułu
from shell.domain.execution.dto.task_execution import TaskExecutionDto
from dataclasses import dataclass
```

## 2. Standard Library — Zawsze z Kanonicznego Źródła

| Nazwa | Import |
|-------|--------|
| `TYPE_CHECKING` | `from typing import TYPE_CHECKING` |
| `Any` | `from typing import Any` |
| `Protocol` | `from typing import Protocol` |
| `dataclass` | `from dataclasses import dataclass` |
| `field` | `from dataclasses import field` |
| `datetime` | `from datetime import datetime` |
| `uuid4` | `from uuid import uuid4` |

**Nigdy** nie importuj tych nazw przez `shell.*` — zawsze bezpośrednio.

## 3. Kolejność i Struktura Importów w Pliku

```python
from __future__ import annotations          # 1. zawsze pierwsza linia

from typing import TYPE_CHECKING, Any       # 2. stdlib (w tym typing)
from dataclasses import dataclass
from datetime import datetime
import uuid

from shell.domain.execution.dto.task_execution import TaskExecutionDto  # 3. projekt: domain
from shell.application.execution.dto import CreateExecutionCommand       # 4. projekt: application

if TYPE_CHECKING:                            # 5. TYPE_CHECKING blok na końcu
    from shell.infrastructure.repositories import ExecutionRepository
    from shell.domain.platform.ports import IdGenerator
```

## 4. Importy Zawsze na Górze Pliku (Module-Level)

Wszystkie importy (zarówno runtime, jak i `TYPE_CHECKING`) są na górze pliku, przed jakimkolwiek kodem.

```python
# DOBRZE
from __future__ import annotations
from typing import TYPE_CHECKING, Any
from dataclasses import dataclass

if TYPE_CHECKING:
    from shell.domain.foo import Bar

class MojaKlasa:
    ...

# ŹLE — import wewnątrz funkcji/metody
class MojaKlasa:
    def metoda(self) -> None:
        from shell.domain.foo import Bar  # NIE
        ...
```

Jedyny wyjątek: `TYPE_CHECKING` wewnątrz strażnika (to wciąż jest na górze pliku, tylko w bloku warunkowym).

## 5. TYPE_CHECKING — Tylko dla Typów Nieużywanych w Runtime

- `from __future__ import annotations` — ZAWSZE obecny → wszystkie adnotacje to stringi, nie potrzebują runtime'owych importów.
- W `if TYPE_CHECKING:` wrzucaj WSZYSTKO, co jest używane **tylko** w adnotacjach typów.
- Na zewnątrz strażnika trzymaj tylko to, co jest faktycznie używane w runtime (w `__init__`, `__slots__`, properties, method bodies).
- Mypy i tak widzi importy z `TYPE_CHECKING` — one muszą być poprawne.

## 6. Gdy Dodajesz Typ, Dodaj Import

Zmieniasz `dict` na `dict[str, Any]`? → `from typing import Any` musi być w pliku.
Dodajesz `| None` w typie? → `from __future__ import annotations` już jest (jeśli nie, dodaj).
Używasz `Protocol`? → `from typing import Protocol`.

Lista kontrolna:
- `Any` → `from typing import Any`
- `Protocol` → `from typing import Protocol`
- `Callable[[...], ...]` → `from typing import Callable`
- `Sequence`, `Mapping`, `Iterable` → z `typing` lub `collections.abc`
- `Self` → `from typing import Self`

## 7. `__init__.py` — Tylko Publiczne API Pakietu

- `__init__.py` re-eksportuje TYLKO nazwy zdefiniowane w tym pakiecie, które są publicznym API.
- `__init__.py` NIGDY nie re-eksportuje nazw z biblioteki standardowej.
- `__init__.py` NIGDY nie re-eksportuje nazw z podpakietów, które konsument może zaimportować bezpośrednio.
- Każdy `__init__.py` ma `__all__`.

## 8. Warstwy — Tylko Dozwolone Kierunki

- `domain/` → NIGDY nie importuje `application.*` ani `infrastructure.*`
- `application/` → importuje `domain.*`, NIGDY `infrastructure.*`
- `infrastructure/` → importuje `domain.*` i `application.*`

## 9. Sytuacja Bez Wyjścia — Zapytaj Użytkownika

Jeśli nie da się zastosować powyższych reguł bez zmiany istniejącej architektury (np. plik `__init__.py` jest jedynym miejscem gdzie dana nazwa jest dostępna, albo import z definiującego modułu powoduje cykl, albo warstwy są wymieszane w sposób którego nie da się rozplątać w ramach tej edycji):

**NIE rób nic na siłę. Zapytaj użytkownika co zrobić.**

Przykłady:
- "Ten import idzie z `__init__.py`, ale definiujący moduł nie jest bezpośrednio dostępny bez cyklu. Jak mam to rozwiązać?"
- "Ten plik w `domain/` importuje z `application/`, ale nie mogę tego zmienić bez refaktoryzacji całego modułu. Zostawić czy przenieść?"
- "W tym pliku TYPE_CHECKING jest na dole, ale są też importy runtime'owe rozrzucone po funkcjach. Poprawić wszystkie czy tylko to co edytuję?"

Zasada: **lepiej zapytać niż wygenerować zmiany które user będzie musiał cofać.**

## 10. Procedura przy Każdej Edycji Importów

1. Czy nazwa jest z stdlib? → import z kanonicznego źródła (reguła 2)
2. Czy nazwa jest z projektu? → znajdź plik `.py` gdzie jest zdefiniowana (class/enum/func), importuj stamtąd (reguła 1)
3. Czy jest używana tylko w typach? → `if TYPE_CHECKING:` (reguła 5)
4. Czy wszystkie użyte typy mają import? → sprawdź (reguła 6)
5. Czy `__init__.py` re-eksportuje stdlib? → usuń (reguła 7)
6. Czy kierunek importu łamie warstwy? → popraw (reguła 8)
7. Nie da się? → reguła 9 — zapytaj użytkownika
