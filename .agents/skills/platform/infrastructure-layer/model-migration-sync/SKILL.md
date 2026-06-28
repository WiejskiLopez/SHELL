---
name: model-migration-sync
description: Reguły utrzymywania zgodności kolumn między SQLAlchemy Model a migracją Alembic — każda zmiana w ORM modelu wymaga aktualizacji odpowiedniej migacji.
---

# Model-Migration Sync

> Umiejętność utrzymywania zgodności definicji kolumn między SQLAlchemy ORM Model a migracją Alembic, która tę tabelę tworzy.

## Dlaczego to jest potrzebne

Gdy zmieniasz nazwę kolumny w modelu SQLAlchemy (np. `kind` → `direction`), ale nie aktualizujesz migracji Alembic która tę tabelę tworzy, baza danych będzie miała starą nazwę kolumny. W efekcie `INSERT` / `SELECT` przez ORM failują z `OperationalError: table X has no column named Y`.

To jest częsty błąd w projektach gdzie modele ORM są refaktorowane, a migracje pisane ręcznie (nie generowane przez `--autogenerate`).

## Reguła 1: Każda zmiana kolumny w modelu = aktualizacja migracji

Jeśli zmieniasz nazwę kolumny w ORM modelu:

```python
# OLD
class TaskExecutionStateModel(Base):
    kind: Mapped[str] = mapped_column()

# NEW
class TaskExecutionStateModel(Base):
    direction: Mapped[str] = mapped_column()
```

To MUSISZ zaktualizować migrację Alembic która tę tabelę tworzy:

```python
# migration/versions/034_....py
sa.Column("direction", sa.String(16), nullable=False),   # ← nie "kind"
```

Gdzie znaleźć właściwą migrację:
1. Znajdź `__tablename__` modelu (np. `task_execution_state`)
2. Wyszukaj w `versions/` migrację która robi `op.create_table("task_execution_state", ...)`
3. Zaktualizuj kolumny w `create_table` aby zgadzały się z modelem

## Reguła 2: Nowa tabela = nowa migracja

Każda nowa tabela w modelu SQLAlchemy wymaga nowej migracji Alembic z `op.create_table()`.

```python
# Nowy model
class GraphNodeExecutionStateModel(Base):
    __tablename__ = "graph_node_execution_state"
    # ...

# Wymaga nowej migracji 042_....py
def upgrade() -> None:
    op.create_table("graph_node_execution_state", ...)
```

## Reguła 3: Downgrade musi być symetryczny

Operacja `downgrade()` w migracji powinna odwracać `upgrade()` — tworzyć stare tabele, przenosić dane z powrotem, używać starych nazw kolumn.

Przykład downgrade'u po zmianie nazwy kolumny:
```python
def downgrade() -> None:
    # Odtwórz starą tabelę z starą nazwą kolumny
    op.create_table(
        "task_execution_state",
        sa.Column("kind", sa.String(16), nullable=False),   # ← stara nazwa
        # ...
    )
    # Przenieś dane z nowej nazwy do starej
    op.execute("""INSERT INTO task_execution_state (... kind ...)
                   SELECT ... direction ... FROM old_table""")
```

## Reguła 4: Weryfikacja — Testuj pełną ścieżkę migracji

Po zmianie migracji uruchom test który:
1. Aplikuje wszystkie migracje od `base` do `head` na świeżej bazie SQLite
2. Tworzy instancję modelu i zapisuje do bazy
3. Odczytuje z bazy i weryfikuje dane

```bash
# Test integracyjny z SQLite powinien to robić automatycznie
python -m pytest shell/tests/...integration/... -v
```

## Reguła 5: Nie modyfikuj opuszczonych (orphan) tabel bez modelu

Jeśli istnieje tabela w `versions/` ale nie ma dla niej modelu SQLAlchemy:
- To jest **orphan table** — nikt z niej nie czyta ani nie pisze przez ORM
- Można ją usunąć w nowej migracji, albo zignorować
- Nie twórz nowego modelu dla takiej tabeli — zrefactoruj ją do wzorca `direction`/`state_data`

## Znajdowanie niezgodności

Uruchom skrypt weryfikacyjny:

```python
# Dla każdego modelu z __tablename__:
#   Znajdź migrację która tworzy tę tabelę
#   Porównaj kolumny w modelu vs w migration.create_table
#   Wypisz różnice
```

Przykładowe niezgodności które ten skill wyłapuje:

| Model (kolumna) | Migracja (kolumna) | Skutek |
|---|---|---|
| `direction` | `kind` | `OperationalError: no column named direction` |
| `state_data` | `payload` | `OperationalError: no column named state_data` |
| Tabela `X` w modelu | Brak `create_table("X")` | `OperationalError: no such table` |
