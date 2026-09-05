---
name: model-migration-sync
description: Reguły utrzymywania zgodności kolumn między SQLAlchemy Model a migracją Alembic — każda zmiana w ORM modelu wymaga aktualizacji odpowiedniej migacji.
---

# Model-Migration Sync

> Umiejętność utrzymywania zgodności definicji kolumn między SQLAlchemy ORM Model a migracją Alembic, która tę tabelę tworzy.

## KARDYNALNA ZASADA: tylko statyczne migracje per tabela — zero legacy

W SHELL jedynym dozwolonym wzorcem migracji są **statyczne pliki Alembic per tabela** w stylu:
`<właściciel>_000N_<tabela>.py` z ręcznym `op.create_table(...)` / `op.drop_table(...)`.

Zakazane (legacy, do usunięcia, nigdy nie przywracać):

- dynamiczne baseline'y aplikujące cały schemat z ORM metadata — `apply_baseline`,
  `revert_baseline`, `apply_delivery_baseline`, `create_service_tables`, `drop_service_tables`,
  `create_service_delivery_tables`, `drop_service_delivery_tables`, `create_all`;
- jakakolwiek "stara kompatybilność" w zawartości migracji;
- mieszanie wzorca statycznego z dynamicznym w jednym pliku.

Każda nowa tabela = nowy statyczny plik `op.create_table`. Tabele delivery
(outbox/inbox/audit/worker_heartbeat) są wspólne z platformą: definiuje je
łańcuch `platform_0001_...` w `shell/platform/infrastructure/persistence/migrations/sql/versions/`,
a każdy serwis dostaje je przez ten łańcuch przed swoim łańcuchem domenowym.

Tabele **sagi** (`saga_instance`/`saga_timeout`) nie są częścią platformy bazowej — to
opcjonalna capability biblioteki `saga-orchestration` (`packaging/saga-orchestration`).
Włącza się ją jawnie (`include_saga=True` w `run_platform_baseline`); serwis adoptuje
tabele własną migracją adopcyjną (wzorzec `project_0004_saga_capability_adopted`), a
referencyjny łańcuch migracji żyje w bibliotece (`saga_0001`/`saga_0002`). Historyczne
`platform_0008_saga_instance`/`platform_0009_saga_timeout` pozostają w platformie wyłącznie
dla kompatybilności baz, które je już wykonały.

Refaktor na statyczny wzorzec wykonuje się **do końca**: nie zostawia się ani jednego pliku
w starym wzorcu, ani jednego wyjątku w regułach architektury. Strażnik
`test_regressions__test_migration_baselines_use_orm_metadata` to egzekwuje: migracja zawierająca
wywołanie dynamicznych helperów jest naruszeniem CRITICAL.

## Jak działa łańcuch i automatyczne wykonywanie

Każdy serwis w `migrations/baseline.py` (np. `run_user_baseline`) wykonuje **dwa łańcuchy
w jednej bazie**:

1. `run_platform_baseline(url, reset_db)` = `alembic upgrade head` na wspólnym łańcuchu
   platformy (`platform/.../migrations/sql/`, tabele delivery),
2. własny łańcuch domenowy (`run_versioned_migrations` / `command.upgrade head` na
   `<serwis>/migrations/`).

**Nowy plik migracji platformy wykonuje się automatycznie** — bez żadnej rejestracji:
przy każdym starcie serwisu/seedzie/teście `run_*_baseline` `upgrade head` sięga po nowy head
i aplikuje tylko nowe rewizje. NIE jest wymagane żadne powiązanie z serwisami.

Warunki poprawnego działania nowego pliku:

1. **Łańcuch liniowy** — `down_revision` nowego pliku = bieżący head łańcucha
   (obecnie `platform_0009_saga_timeout`), a `revision = "platform_0010_<opis>"`.
   Nie wolno tworzyć drugiego head (rozgałęzienia/mergi bez scalań), bo `upgrade head`
   wtedy rzuci błędem *ambiguous*. Zweryfikuj: `alembic history base:head`.
2. **Statyczny DDL per tabela** — `op.create_table`/`op.drop_table`, bez dynamicznych helperów
   (patrz KARDYNALNA ZASADA). Strażnik to egzekwuje.
3. **Downgrade symetryczny** (Reguła 3).

Na bazach, gdzie łańcuch był już zastosowany, własna tabela wersji `platform_alembic_version`
(dbita przez `env.py` platformy) pilnuje, by wykonał się **tylko nowy plik**, a nie cały łańcuch
od nowa. Serwis używa domyślnej `alembic_version` — dwa łańcuchy w jednej bazie nie kolidują
(aplikacja, `reset_db` = downgrade/upgrade każdego z osobna).

Head serwisu to **ostatnia migracja domenowa** (łamiesz łańcuch serwisu na ostatniej tabeli
domenowej; serwis NIE zawiera tabel delivery — te zawsze idą z platformy). Serwis z capability
sagi zawiera w swoim łańcuchu migrację adopcyjną tabel sagowych (`project_0004_saga_capability_adopted`).

## Dlaczego to jest potrzebne

Zmiana nazwy kolumny w modelu SQLAlchemy (np. `kind` → `direction`) wymaga aktualizacji
migracji Alembic, która tę tabelę tworzy; rozbieżność skutkuje
`OperationalError: table X has no column named Y` przy `INSERT`/`SELECT` przez ORM.

Występuje często przy ręcznie pisanych migracjach (bez `--autogenerate`) podczas refaktoru
modeli ORM.

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
sa.Column("direction", sa.String(16), nullable=False),   # ← 'direction' (zgodnie z modelem)
```

Gdzie znaleźć właściwą migrację:
1. Znajdź `__tablename__` modelu (np. `task_execution_state`)
2. Wyszukaj w `versions/` migrację która robi `op.create_table("task_execution_state", ...)`
3. Zaktualizuj kolumny w `create_table` aby zgadzały się z modelem

## Reguła 2: Nowa tabela = nowa migracja

Każda nowa tabela w modelu SQLAlchemy wymaga nowej migracji Alembic z `op.create_table()`.

```python
# Nowy model
class NodeExecutionStateModel(Base):
    __tablename__ = "node_execution_state"
    # ...

# Wymaga nowej migracji 042_....py
def upgrade() -> None:
    op.create_table("node_execution_state", ...)
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

## Reguła 5: Orphan table obsługiwane przez istniejący model

Tabela w `versions/` korzysta z odpowiadającego modelu SQLAlchemy:
- **Orphan table** — tabela bez odczytu/zapisu przez ORM — jest usuwana w nowej migracji albo pomijana
- Refaktoryzacja opiera się na wzorcu kolumn `direction`/`state_data` w istniejącym modelu; nowy model dla takiej tabeli nie powstaje

## Nazewnictwo plików migracji

- Nazwa pliku: `<właściciel>_<numer>_<tabela>.py` — statyczna migracja per tabela
  (np. `scheduling_0001_scheduler_definition.py`, `user_0002_user_state.py`).
- Kolejna ewolucyjna zmiana na istniejącej tabeli: `<właściciel>_<numer>_<opis>.py`
  (np. `project_0004_add_repo_url.py`).
- Migracje wspólne (platforma) noszą prefiks `platform_`: `platform_0010_<tabela>.py`.
- Numer w nazwie jest wyłącznie porządkiem czytelności; łańcuch budują pola `revision` /
  `down_revision` (Alembic nie zależuje od nazwy pliku).

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
