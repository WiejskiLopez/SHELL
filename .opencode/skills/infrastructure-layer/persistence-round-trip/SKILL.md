---
name: persistence-round-trip
description: Reguły testów round-trip persystencji — każde pole zmieniane po utworzeniu agregatu musi przejść obie strony mappera (entity → model → entity) na bazie utworzonej migracjami. Używaj gdy zmieniasz pole agregate z persystencją, dodajesz mapper, albo refaktoryzujesz `restore()`/`_new()`.
---

# Persistence Round-Trip — pole zmieniane po `new()` musi przetrwać reload

## 1. Problem

Architektura sprawdza strukturę maperów („nie ma logiki biznesowej", „są oba kierunki"),
ale to **nie łapie zagubionego pola**. Błąd polega na tym, że:

- `entity → model` **zapisuje** pole (`model.status = entity.status.value`),
- `model → entity` / `restore()` **nie odczytuje** tego pola (nie ma go w sygnaturze `restore` lub
  w wywołaniu), więc powstały po reloadzie agregat ma domyślny/zerowy stan.

Przykład wykryty w SHELL: `GraphExecution.entity_to_model` zapisywał `status`, ale
`GraphExecution.restore()` nie przyjmował `execution_status` — po restarcie workera graf zawsze
wracał `PENDING`, mimo że był `COMPLETED`.

## 2. Sygnały ostrzegawcze

Szukaj pól, które są:

- w `__slots__` agregatu i nadawane poza konstruktorem (`start()`, `complete()`, `change_status()`,
  `mark_deleted()` itd.);
- zapisywane w mapperze `*_entity_to_model.py`;
- ale **nieobecne w sygnaturze `restore()`** ani w mapperze `*_model_to_entity.py`.

Jeśli `restore()` nie przyjmuje pola, które `_new()/create()` po nadaniu zmienia — jest to utrata stanu.

## 3. Kontraktowy test round-trip

Test nie może być wyłącznie „składnia/importy" — musi wykonać faktyczny cykl:

```
entity → model → (baza utworzona przez migracje) → model → entity
```

i porównać pole zmieniane po utworzeniu:

```python
async def test_round_trip_preserves_execution_status(session_factory):
    original = GraphExecution.initialize(...)
    original.change_status(GraphExecutionStatus.COMPLETED, now)
    await sql_repo.save(original)          # entity → model → INSERT (schema z migracji)
    restored = await sql_repo.get_by_id(original.id)  # SELECT → model → entity
    assert restored.status is GraphExecutionStatus.COMPLETED
```

Wymaganie: baza musi powstać przez **migracje** (baseline), nie `create_all` obok — inaczej test
nie dowodzi zgodności istniejącej bazy z modelem ORM.

## 4. Reguła dla `restore()`

- `restore()` musi przyjmować **wszystkie pola zmieniane po utworzeniu** agregatu.
- Domyślne wartości w `restore()` (np. `execution_status=PENDING`) są dozwolone tylko tam, gdzie
  to faktyczna wartość „dla starego wiersza"; używaj ich świadomie.
- Mapper `model → entity` musi przekazywać każde pole, które `entity → model` zapisuje.

## 5. Checklista

Podczas zmiany pola w agregacie persystowanym:

- [ ] Pole jest w `__slots__` agregatu
- [ ] `entity_to_model` je zapisuje
- [ ] `model_to_entity` je odczytuje i przekazuje do `restore()`
- [ ] `restore()` przyjmuje to pole (albo jest to świadoma wartość domyślna dla legacy)
- [ ] InMemory storage nie gubi pola (np. `copy.deepcopy` przy zwrocie)
- [ ] Test round-trip na bazie z migracji porównuje pole po pełnym cyklu
- [ ] Test restartu/reloadu w ścieżkach process dla pól decyzyjnych (status, liczniki, wyniki)