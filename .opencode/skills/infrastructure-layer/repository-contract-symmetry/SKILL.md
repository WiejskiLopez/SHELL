---
name: repository-contract-symmetry
description: Reguły symetrii kontraktu adapterów repozytorium — adapter SQL i InMemory muszą mieć identyczną obserwowalną semantykę dla każdej metody portu. Lookupy po nieunikalnym kluczu, obsługa soft-delete VO oraz pełna implementacja portu. Używaj gdy projektujesz nowy port repozytorium, refaktoryzujesz adapter, albo podejrzewasz, że InMemory maskuje błąd SQL (lub odwrotnie).
---

# Repository Contract Symmetry — InMemory = SQL

## 1. Zasada nadrzędna

**Ten sam port musi mieć identyczną, obserwowalną semantykę w obu adapterach.**

Każda metoda portu repozytorium jest weryfikowana w parze (SQL + InMemory) przez test
kontraktowy. Asymetria prowadzi do: testów jednostkowych przechodzących na fałszywym
adapterze i błędu dopiero z prawdziwą bazą (lub odwrotnie — repozytorium InMemory zepsute,
a SQL poprawne).

## 2. Lookup po nieunikalnym kluczu (FK, `name`, `workflow_id`)

Kolumna bez `unique` może zwracać wiele wierszy. Metoda portu ZWRACAJĄCA POJEDYNCZY rekord
(„`get_by_*` → aggregate | None") musi być deterministyczna:

- **SQL**: `ORDER BY <id>.asc().limit(1)`; goły `scalar_one_or_none()` po nieunikalnym kluczu grozi `MultipleResultsFound`.
- **InMemory**: jawna kolekcja kandydatów + `min(kandydaci, key=id.value)`; wybór „pierwszego pasującego"
  w kolejności `dict` pozostaje poza wzorcem.

```python
# SQL — deterministyczny
query = (
    select(Model)
    .where(Model.name == value)
    .order_by(Model.id)
    .limit(1)
)
row = (await session.execute(query)).scalar_one_or_none()

# InMemory — ten sam wybór
matches = [e for e in self._store.values() if e.name == value]
return min(matches, key=lambda e: e.id.value) if matches else None
```

Unikalność w bazie (`unique=True`) znosi wymóg deterministycznego wyboru (np. `user.email`);
przy braku constraintu determinizm jest obowiązkowy.

## 3. Soft-delete VO (`_deleted_at`)

`_deleted_at` na agregacie to Value Object (`DeletedAt`) z wartością domyślną
`DeletedAt(value=None)`; porównania używają zawsze `.value`:

- poprawne: `entity.deleted_at.value is None`
- antywzorzec: `entity.deleted_at is None`

To samo dotyczy generycznego base InMemory:

```python
async def exists(self, id) -> ExistsResult:
    entity = self._store.get(key)
    if entity is None:
        return ExistsResult(False)
    deleted = getattr(entity, "_deleted_at", None)
    if deleted is None:          # slot nieustawiony — istnieje
        return ExistsResult(True)
    return ExistsResult(deleted.value is None)  # VO — sprawdź .value
```

## 4. Kompletność portu po obu stronach

Port (Protocol) bywa szerszy niż adapter; adapter implementuje **każdą** metodę portu.
Metody tylko deklarowane („luka dostarczy runtime") skutkują błędem dopiero w runtime, a mypy
przy strukturalnym Protocol nie wykryje braku metody. Przy refaktorze portu od razu:

1. przeszukaj oba adaptery (SQL + InMemory) pod `get_next_pending`/`delete`/`exists` itd.;
2. brakująca metoda albo dostaje pełną implementację (port musi być spełniony),
   albo jest usuwana z portu;
3. dodaj test kontraktowy dla każdej metody portu na obu adapterach.

## 5. Metody listujące — deterministyczna kolejność

Metody zwracające listy, z których framework wybiera `result[0]`, muszą mieć deterministyczny
`ORDER BY` (SQL) i równoważne sortowanie (InMemory). Bez tego wybór pierwszego elementu
różni się między SQLite a PostgreSQL i różnymi planami zapytań.

## 6. Checklista przy projektowaniu/refaktorze portu repozytorium

- [ ] Porównaj SQL i InMemory metodę-po-metodzie dla WSZYSTKIEGO portu
- [ ] Lookup po nieunikalnym kluczu: `ORDER BY id LIMIT 1` (SQL) / `min(by id)` (InMemory)
- [ ] Soft-delete: porównuj przez `.value is None`
- [ ] Każda metoda portu działa w obu adapterach (SQL + InMemory)
- [ ] Test kontraktowy per metoda (obie ścieżki: znaleziono / nie znaleziono / wiele wyników)
- [ ] Metoda listująca wybierana przez `[0]` ma deterministyczne sortowanie