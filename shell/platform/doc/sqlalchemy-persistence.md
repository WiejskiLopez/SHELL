# Persistence SQLAlchemy

## Cel / Co realizuje

Warstwa persistence SQL jest zbudowana na SQLAlchemy 2.0 (async: `AsyncSession`/`create_async_engine`) i składa się z: bazowego `Base` (per bounded context), kompatybilnego typu `JSONB`, dekoratora `JsonStrType` (most między domenowym `JsonStr` a kolumną JSON), mixinów `TimestampedMixin`/`VersionedMixin`, fabryki sesji `build_session_factory` oraz rodziny `InMemoryRepository`/fakes do testów bez bazy. Dla testów pamięciowych istnieje alternatywny, w pełni platformowy adapter `persistence/memory`.

## Problem

Agregaty DDD operują na domenowych Value Objectach (w tym `JsonStr` — zwalidowany JSON jako string), a baza danych wymaga typów SQL (`JSONB`, `TIMESTAMP`, `INTEGER`). Bez mapowania typów każdy BC musiałby powtarzać konwersję, a kolumny audytowe (`created_at`, `updated_at`, `deleted_at`) i optymistyczne blokowanie (`version`) byłyby definiowane niespójnie. Dodatkowo testy jednostkowe warstwy aplikacji nie mogą zależeć od działającej bazy — potrzebne są deterministyczne repozytoria i fake'i w pamięci.

## Realizacja techniczna

### Bazowy model per BC

`SqlAlchemyModelBase(DeclarativeBase)` w `shell/platform/infrastructure/persistence/sql/models/base.py` jest eksportowany jako alias `Base`. Każdy bounded context tworzy **własny** podklasowy `Base` w swoim module models (np. `shell/<bc>/infrastructure/<bc>/persistence/sql/models/base.py`) i wiąże do niego wszystkie swoje modele — każdy BC ma niezależny rejestr `metadata`, dzięki czemu tabele różnych BC nie kolidują ze sobą.

### Typ JSONB (`_compat.py`)

`JSONB = JSON().with_variant(_PgJSONB(), "postgresql")` — abstrakcja dialektu: na PostgreSQL używany jest natywny `JSONB`, wszędzie indziej (SQLite) generyczny `JSON`. Dzięki temu ten sam kod modelu działa na obu silnikach bez zmian.

### `JsonStrType` — most między domeną a kolumną

`JsonStrType(TypeDecorator[JsonStr])` (`json_str_type.py`) z `impl = JSONB` i `cache_ok = True`:

- `process_bind_param(value)` — przy zapisie sparsowuje `JsonStr` (lub `str`) przez `json.loads` i przekazuje do kolumny obiekt JSON; dla `None` zwraca `None`;
- `process_result_value(value)` — przy odczycie serializuje z powrotem `json.dumps(value)` do `JsonStr`.

Domenowy typ `JsonStr` (frozen dataclass w `shell/platform/types/json_str.py`) waliduje w `__post_init__`, że wartość jest niepustym, poprawnym JSON. `JsonStrType` jest jedynym mostem między światami — obiekt JSON istnieje tylko przejściowo na granicy adaptera DB.

### Mixiny

- `TimestampedMixin` (`mixins/timestamped.py`): dodaje `created_at: Mapped[datetime]` (nullable=False), `updated_at: Mapped[datetime]` (nullable=False), `deleted_at: Mapped[datetime | None]` (nullable=True, default=None). Uwaga w docstringu: model, który sam definiuje `created_at`, nie może dziedziczyć mixinu — SQLAlchemy nie pozwala nadpisywać kolumn z mixinów; musi dodać `updated_at`/`deleted_at` ręcznie.
- `VersionedMixin` (`mixins/versioned.py`): dodaje kolumnę `version: Mapped[int]` (nullable=False, default=1). Mixin **nie** ustawia `__mapper_args__` — każda klasa go dziedzicząca MUSI sama ustawić `__mapper_args__ = {"version_id_col": version}` (np. przez `@declared_attr`), bo SQLAlchemy nie dziedziczy `__mapper_args__` z mixinów. To włącza optymistyczne blokowanie (version_id_col) dla współbieżnych zapisów.

### Sesja — `build_session_factory`

`build_session_factory(url: str) -> async_sessionmaker[AsyncSession]` w `shell/platform/infrastructure/persistence/sql/__init__.py`:

- `create_async_engine(url, echo=False, future=True)`; dla URL-i zawierających `"sqlite"` ustawia `connect_args={"check_same_thread": False}` (wymóg aiosqlite);
- zwraca `async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)` — `expire_on_commit=False`, by agregaty pozostawały użyteczne po commicie;
- `get_session(session_factory)` — generator async zwracający pojedynczy `AsyncSession` (do użycia z `Depends`).

### InMemoryRepository

`InMemoryRepository(Generic[TAggregate, TId])` w `shell/platform/infrastructure/persistence/in_memory_repository.py` — bazowa implementacja oparta o `self._store: dict[str, TAggregate]`:

- `get_by_id(id)` / `save(entity)` — klucz to `id.value` (dla VO) albo `str(id)`;
- `all()` — kopia wszystkich agregatów (włącznie z soft-deleted);
- `delete(id, now=None)` — soft-delete przez `object.__setattr__(entity, "_deleted_at", DeletedAt.from_datetime(dt))` (obejście frozen dataclass);
- `exists(id)` — zwraca `ExistsResult(False)` dla nieobecnych i soft-deleted.

Konkretne podklasy per BC (np. `InMemoryGraphExecutionStateInputRepository`, `InMemoryQueryServices`) dodają tylko metody zapytań specyficzne dla BC.

### Fakes w `persistence/memory`

`shell/platform/infrastructure/persistence/memory/` zawiera platformowe fake'i (wyłącznie do testów):

- `FakeClock(fixed)` — `now()` zwraca stały czas;
- `FakeEventPublisher` — gromadzi `self.published: list[object]`;
- `FakeMessagePublisher` — analogiczny dla wiadomości;
- `FakeIdGenerator` — sekwencyjne UUID-kształtne id (`f"00000000-0000-0000-0000-{counter:012d}"`) przez `new_id(id_type)`;
- `FakeLogger` — no-op implementacja portu `Logger`;
- `FakeTaskLoader` — loader zadań.

Wszystkie są eksportowane przez `shell/platform/infrastructure/persistence/memory/__init__.py`.

## Kluczowe pliki

- `shell/platform/infrastructure/persistence/sql/models/base.py`
- `shell/platform/infrastructure/persistence/sql/models/_compat.py`
- `shell/platform/infrastructure/persistence/sql/models/json_str_type.py`
- `shell/platform/infrastructure/persistence/sql/models/mixins/timestamped.py`
- `shell/platform/infrastructure/persistence/sql/models/mixins/versioned.py`
- `shell/platform/infrastructure/persistence/sql/__init__.py`
- `shell/platform/infrastructure/persistence/in_memory_repository.py`
- `shell/platform/infrastructure/persistence/memory/`
- `shell/platform/types/json_str.py`

## Powiązane koncepcje

- [unit-of-work](unit-of-work.md)
- [delivery-models](delivery-models.md)
- [ports-and-adapters](ports-and-adapters.md)
- [architecture-overview](architecture-overview.md)
