---
name: noqa-enterprise-policy
description: Zasady stosowania dyrektywy # noqa w aplikacjach enterprise — kiedy wolno, kiedy nie wolno, obiektywne kryteria uniwersalne. Używaj gdy review'ujesz kod z # noqa, projektujesz politykę lintera dla nowego projektu, lub zastanawiasz się czy dany warning powinien być naprawiony czy stłumiony.
---

# # noqa w aplikacjach enterprise — polityka zero zaskoczeń

`# noqa` to mechanizm tłumienia ostrzeżeń lintera (`ruff`, `flake8`, `pylint`). W kodzie enterprise każda taka dyrektywa jest świadomą decyzją architektoniczną, nie obejściem. Ten skill opisuje obiektywne kryteria: kiedy `# noqa` jest akceptowalne, kiedy jest niedopuszczalne, i jak je dokumentować.

---

## Złota zasada

> **Każde `# noqa` bez uzasadnienia to błąd. Każde `# noqa` z uzasadnieniem to decyzja.**

Linter nie zna kontekstu biznesowego. `# noqa` mówi: "rozumiem o co pyta linter, ale w TYM KONKRETNYM MIEJSCU świadomie podejmuję inną decyzję — oto dlaczego".

---

## Kiedy `# noqa` jest NIEDOPUSZCZALNE

Poniższe przypadki to nadużycia — kod musi być naprawiony, nie stłumiony.

### 1. Maskowanie martwego kodu

```python
# ❌ NIEDOPUSZCZALNE
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    return total
    unused_var = 42  # noqa: F841
```

Nieużywana zmienna to albo bug (zapomniano jej użyć), albo martwy kod do usunięcia. `# noqa` nie jest alternatywą dla usunięcia.

### 2. Maskowanie błędów typowania

```python
# ❌ NIEDOPUSZCZALNE
def process(data: dict) -> str:
    return data["key"].upper()  # noqa: E501
```

Jeśli `data["key"]` może być `None`, to `# noqa` nie naprawi `AttributeError` w produkcji. Kod musi być bezpieczny typowo.

### 3. Tłumienie warningów hurtowo

```python
# ❌ NIEDOPUSZCZALNE
# noqa: F401,F403,F405,F811,F841
import os
import sys
from somewhere import *  # noqa
```

Tłumienie wielu reguł naraz bez wyjaśnienia każdej z osobna maskuje nieznane problemy.

### 4. Unikanie refaktoryzacji

```python
# ❌ NIEDOPUSZCZALNE
def do_everything(order_id, user_id, payment_id, shipping_id, email_id, log_id):  # noqa: PLR0913
    # 500 linii kodu...
```

Za dużo parametrów to sygnał, że funkcja robi za dużo. `# noqa` nie zastąpi podziału na mniejsze funkcje.

### 5. Gołe `# noqa` bez kodu reguły

```python
# ❌ NIEDOPUSZCZALNE
x = get_data()  # noqa
```

Brak kodu reguły (`F841`, `E501` itd.) oznacza "wycisz wszystko". To tłumi także przyszłe warningi, które mogłyby wskazać realny błąd.

### 6. `# noqa` na pliku lub całej klasie

```python
# ❌ NIEDOPUSZCZALNE
# flake8: noqa  — wyłącza wszystkie sprawdzenia w całym pliku
```

Wyłączenie lintera na poziomie pliku lub klasy to ukrywanie długu technicznego.

---

## Kiedy `# noqa` jest AKCEPTOWALNE

Poniższe przypadki to uzasadnione użycia — każde wymaga jawnego wyjaśnienia.

### 1. Re-eksport symboli (F401 — unused import)

```python
# ✅ AKCEPTOWALNE
# __init__.py — re-export publicznego API
from .service import UserService  # noqa: F401
from .repository import UserRepository  # noqa: F401

__all__ = ["UserService", "UserRepository"]
```

Import nie jest używany wewnątrz tego pliku, ale jest celowo re-eksportowany dla konsumentów. Linter nie widzi tego kontekstu.

### 2. Framework wymusza import w runtime (TC002, TC003)

```python
# ✅ AKCEPTOWALNE
from datetime import datetime  # noqa: TC003 — SQLAlchemy Mapped[datetime] wymaga runtime

class OrderModel(Base):
    created_at: Mapped[datetime]
```

Mimo że typ jest użyty tylko w adnotacji, framework (SQLAlchemy, Pydantic, FastAPI) potrzebuje go w runtime do introspekcji typów.

### 3. Celowe złamanie circular import (E402)

```python
# ✅ AKCEPTOWALNE
class OrderModel(Base):
    items: Mapped[list["OrderItemModel"]] = relationship(...)

from .order_item import OrderItemModel  # noqa: E402 — łamie circular import Order ↔ OrderItem
```

Dwa moduły wzajemnie się importują. Jedynym rozwiązaniem bez gruntownej przebudowy jest lazy import na końcu pliku.

### 4. Fałszywy pozytyw lintera

```python
# ✅ AKCEPTOWALNE
def __init__(self, name: str) -> None:
    self._name = name  # noqa: B010 — setattr byłby tutaj mniej czytelny
```

Linter sugeruje `setattr`, ale bezpośrednie przypisanie w `__init__` jest idiomatyczne i bezpieczne. To świadoma decyzja stylistyczna.

### 5. Kod generowany / migracje

```python
# ✅ AKCEPTOWALNE
# Alembic migration — nie modyfikuj ręcznie
revision: str = "abc123"  # noqa: F811 — redefinicja wymagana przez Alembic
```

Kod generowany przez narzędzia (Alembic, protobuf, OpenAPI generator) ma własne konwencje. `# noqa` chroni go przed przypadkową modyfikacją.

### 6. Optymalizacja krytyczna wydajnościowo

```python
# ✅ AKCEPTOWALNE
# Funkcja hot-path — rozwinięcie pętli daje 12% wzrost przepustowości
for i in range(0, len(data), 4):  # noqa: PLR1736
    process(data[i])
    process(data[i + 1])
    process(data[i + 2])
    process(data[i + 3])
```

Gdy benchmarki potwierdzają, że idiomatyczny kod jest zbyt wolny, a optymalizacja jest wymagana biznesowo.

---

## Format `# noqa` w enterprise

### Struktura

```
<linia kodu>  # noqa: <KOD_REGUŁY> — <uzasadnienie>
```

| Element | Wymagany | Przykład |
|---------|----------|---------|
| `# noqa:` | tak | `# noqa:` |
| Kod reguły | tak | `E402`, `F401`, `TC002` |
| Uzasadnienie | tak | `łmie circular import A ↔ B` |

### Przykłady poprawne

```python
from .other import OtherModel  # noqa: F401 — re-export dla konsumentów

from datetime import datetime  # noqa: TC003 — SQLAlchemy Mapped[datetime] wymaga runtime

from .order import Order  # noqa: E402 — łamie circular import z OrderModel

data = cache.get(key)  # noqa: B010 — jawne przypisanie czytelniejsze niż setattr w tym kontekście
```

### Przykłady niepoprawne

```python
# ❌ brak kodu reguły
x = foo()  # noqa

# ❌ brak uzasadnienia
from .other import OtherModel  # noqa: F401

# ❌ wiele reguł bez wyjaśnienia każdej
import os  # noqa: F401,F403,F811

# ❌ noqa na całym pliku
# flake8: noqa

# ❌ noqa wewnątrz docstringa (nie działa we wszystkich linterach)
"""Moduł X. # noqa"""
```

---

## Proces review dla `# noqa`

W PR zawierającym `# noqa` reviewer sprawdza:

| Pytanie | Jeśli NIE → |
|---------|-------------|
| Czy komentarz wyjaśnia DLACZEGO? | Odrzuć PR — dodaj uzasadnienie |
| Czy problem da się rozwiązać inaczej? | Wskaż alternatywę, `# noqa` tylko w ostateczności |
| Czy `# noqa` maskuje realny bug? | Odrzuć PR — napraw buga |
| Czy to samo `# noqa` występuje wielokrotnie? | Zaproponuj regułę lintera lub refaktoryzację |
| Czy reguła jest wyłączona globalnie w `pyproject.toml`? | Usuń `# noqa` — globalna konfiguracja wystarczy |

---

## Audyt `# noqa`

Co kwartał (lub sprint):

1. **Policz**: `grep -r "noqa:" . | wc -l`
2. **Przeglądnij trend**: jeśli liczba rośnie szybciej niż kod, coś jest nie tak
3. **Sprawdź martwe noqa**: czy nadal są potrzebne? Linter ewoluuje — co było false-positive rok temu, może być dzisiaj naprawione
4. **Usuń nieaktualne**: jeśli reguła jest już w `pyproject.toml` jako wyłączona globalnie, lokalne `# noqa` jest zbędne

---

## Reguły konfiguracji globalnej vs lokalnej

| Sytuacja | Rozwiązanie |
|----------|-------------|
| Reguła nigdy nie pasuje do stylu projektu | Wyłącz globalnie w `pyproject.toml` |
| Reguła pasuje, ale jest 1-2 wyjątki | `# noqa` w tych miejscach |
| Reguła pasuje, ale wyjątków jest wiele (>10) | Rozważ globalne wyłączenie + dokumentację ADR dlaczego |
| Reguła jest wartościowa, wyjątki są uzasadnione | `# noqa` z uzasadnieniem — to norma |

---

## Antywzorce # noqa

| Antywzorzec | Dlaczego boli | Prawidłowe podejście |
|-------------|--------------|---------------------|
| `# noqa` bez kodu | Wycisza przyszłe warningi | Zawsze podaj konkretny kod: `# noqa: E402` |
| `# noqa` na całym pliku | Wyłącza sprawdzanie wszystkiego | Punktowe `# noqa` na konkretnych liniach |
| `# noqa` jako pierwsze rozwiązanie | Unika konfrontacji z problemem | Najpierw spróbuj naprawić, potem tłumić |
| `# noqa` przed code review | Ukrywa problemy przed reviewerem | Reviewer widzi każde `# noqa` i może je zakwestionować |
| Kopiowanie `# noqa` z innego miejsca | Ten sam kod reguły, inny kontekst | Każde `# noqa` jest decyzją dla TEGO miejsca |
| `# noqa: F403` zamiast `__all__` | Ukrywa brak jawnego API | Dodaj `__all__` z jawnym eksportem |

---

## Konwencje

- Każde `# noqa` zawiera **kod reguły** i **uzasadnienie** oddzielone pauzą
- Uzasadnienie jest w języku projektu (PL lub EN — konsekwentnie)
- `# noqa` jest na TEJ SAMEJ LINII co tłumiony kod
- Dla re-eksportów: uzasadnienie zaczyna się od `re-export`
- Dla circular imports: uzasadnienie zawiera nazwy obu modułów
- Dla framework constraints: uzasadnienie zawiera nazwę frameworka i powód
- W `__init__.py` z re-eksportami: każde `# noqa: F401` jest osobną linią z własnym uzasadnieniem
