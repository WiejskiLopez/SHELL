# SQLAlchemy Index Convention

## Zasada
Indeksy definiujemy **wylacznie w plikach migracji Alembic** (`versions/`).

Mapper ORM (model) nie zawiera zadnych definicji indeksow — ani przez `__table_args__`, ani przez `index=True` w `mapped_column()`.

## Przyklad
```python
from sqlalchemy.orm import Mapped, mapped_column

class MyModel(Base):
    __tablename__ = "my_table"

    id: Mapped[str] = mapped_column(primary_key=True)
    column_a: Mapped[str] = mapped_column(nullable=False)
```

Odpowiadajaca migracja:
```python
op.create_index("ix_my_table_column_a", "my_table", ["column_a"])
```

## Uzasadnienie
- Jedno zrodlo prawdy dla indeksow — pliki migracji
- Mapper ORM opisuje tylko kolumny i relacje
- Testy uruchamiaja pelna migracje (`alembic upgrade head`) zamiast `create_all`, wiec indeksy sa tworzone przez migracje
- Eliminacja ryzyka duplikacji (gdy `index=True` i `__table_args__` definiuja ten sam indeks)
