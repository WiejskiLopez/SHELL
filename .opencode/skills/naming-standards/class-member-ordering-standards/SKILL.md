---
name: class-member-ordering-standards
description: Reguły porządkowania składowych klasy — najpierw publiczne potem prywatne, __slots__ na początku, zasady widoczności.
---

# Class Member Ordering Standards

> Reguły porządkowania składowych w klasie — kolejność i widoczność.

## Złota zasada

**Najpierw publiczne, potem prywatne.** Prywatne składowe zawsze z prefiksem `_`.

```python
class Workflow(AggregateRoot[WorkflowId]):
    # 0. (OPCJONALNIE) __slots__ i __init__ na początku
    __slots__ = ("_status", "_version", ...)

    def __init__(self, id: WorkflowId, ...) -> None:
        self._id = id
        ...

    # 1. PUBLICZNE — metody i properties
    @property
    def status(self) -> Status:
        return self._status

    def start_at(self, now: datetime) -> None:
        ...

    def finish(self, now: datetime) -> None:
        ...

    # 2. PRYWATNE — z prefiksem _
    def _build_sequence_transitions(self) -> None:
        ...
```

## Kolejność

1. `__slots__` (opcjonalnie na początku)
2. `__init__` (opcjonalnie)
3. Metody publiczne i properties
4. Metody prywatne (`_` prefiks)

## Zasady widoczności

1. **Wszystkie prywatne składowe klasy** (`_metoda`, `_atrybut`) występują po wszystkich publicznych.
2. Wyjątek: `__init__` i `__slots__` mogą być na początku klasy (przed publicznymi metodami).
3. **Żadna publiczna metoda nie występuje po prywatnej.**
4. Prywatne atrybuty instancji (`self._nazwa`) zawsze z prefiksem `_`.
5. Używaj `_` (protected) zamiast `__` (name mangling), chyba że potrzebujesz name mangling w podklasach.

## Zakres widoczności — prywatne tylko wewnątrz klasy/pliku

Składowe z prefiksem `_` **mogą być używane wyłącznie wewnątrz klasy która je definiuje** lub — w przypadku funkcji modułu — **wewnątrz tego samego pliku**.

```python
# POPRAWNIE — użycie wewnątrz tej samej klasy
class Workflow:
    def finish(self, now):
        self._transition_to(Status.done())

    def _transition_to(self, status):
        self._status = status

# ŹLE — użycie z zewnątrz
workflow._transition_to(Status.done())  # nie wolno
```

## Wyjątki (dozwolone)

- Testy jednostkowe mogą wołać `_` metody aby zweryfikować stan wewnętrzny — ale tylko w ostateczności, preferuj testowanie przez publiczny API.
- Framework ORM (SQLAlchemy) może wymagać dostępu do `_` pól w mapperach — to akceptowalne w `infrastructure/`.
