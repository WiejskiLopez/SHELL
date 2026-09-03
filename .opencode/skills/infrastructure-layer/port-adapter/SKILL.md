---
name: port-adapter
description: Zasady projektowania Portów i Adapterów w architekturze hexagonalnej — definiowanie portów w domenie/aplikacji, implementacja adapterów w infrastrukturze, granularność portów, testowanie, ewolucja. Używaj gdy definiujesz nowy port (Protocol/ABC), implementujesz adapter, albo refaktoryzujesz istniejącą granicę.
---

# Port & Adapter (Hexagonal) w Enterprise DDD

## 1. Port — Kontrakt w Domenie

**Port** to interfejs (Protocol/ABC) zdefiniowany w warstwie domenowej (lub aplikacyjnej). Definiuje **co** system robi; **jak** realizuje to adapter (implementacja portu w infrastrukturze).

```python
# shell/platform/domain/ports/clock.py — Port w domenie
class Clock(Protocol):
    """Port — dostarcza bieżący czas."""
    def now(self) -> Timestamp: ...

# shell/platform/domain/ports/id_generator.py
class IdGenerator(Protocol):
    """Port — generuje unikalne identyfikatory."""
    def generate(self) -> str: ...

# shell/<service>/domain/execution/aggregates/<agregat>/repositories/execution_repository.py — Port repozytorium
class ExecutionRepository(ABC):
    @abstractmethod
    async def get(self, id: ExecutionId) -> Execution: ...
    @abstractmethod
    async def save(self, execution: Execution) -> None: ...
```

## 2. Adapter — Implementacja w Infrastrukturze

**Adapter** implementuje port w warstwie infrastruktury.

```python
# shell/platform/infrastructure/time/system_clock.py
    class SystemClock:
        """Adapter — implementuje Clock przez systemowy zegar."""
        def now(self) -> Timestamp:
            return Timestamp.now()

# shell/platform/infrastructure/identity/uuid_id_generator.py
    class UuidIdGenerator:
        """Adapter — implementuje IdGenerator przez UUID."""
        def generate(self) -> str:
            return str(uuid4())

# shell/<service>/infrastructure/execution/<aggregate>/persistence/sql/repositories/sql_execution_repository.py
    class SqlExecutionRepository(ExecutionRepository):
        """Adapter — implementuje ExecutionRepository przez SQLAlchemy."""
        ...
```

## 3. Port Należy do Potrzebującego (Domena/Aplikacja)

Port jest własnością tego, kto GO POTRZEBUJE. Jeśli domena potrzebuje czasu → port `Clock` jest w domenie.

```python
# Port jest w domenie, bo to DOMENA potrzebuje czasu
# shell/platform/domain/ports/clock.py
class Clock(Protocol):
    def now(self) -> Timestamp: ...

# Adapter w infrastrukturze
# shell/platform/infrastructure/time/system_clock.py
class SystemClock:
    def now(self) -> Timestamp:
        return Timestamp(datetime.now(tz=UTC))
```

## 4. Granularność Portów

| Granularność | Kiedy użyć | Przykład |
|-------------|-----------|----------|
| **Jeden port na operację** | Operacja jest złożona | `FileStorage` (store, retrieve, delete) |
| **Jeden port na serwis** | Serwis ma wiele powiązanych operacji | `NotificationService` (send_email, send_sms, send_push) |
| **Jeden port = jedna metoda** | Operacja jest prosta, izolowana | `Clock`, `IdGenerator` |

```python
# Zbyt duży port
class FileStorage(Protocol):
    async def store(self, path: str, content: bytes) -> None: ...
    async def retrieve(self, path: str) -> bytes: ...
    async def delete(self, path: str) -> None: ...
    async def list(self, prefix: str) -> list[str]: ...
    async def exists(self, path: str) -> bool: ...

# Dobry port — odpowiedzialność: przechowywanie plików
class FileStorage(Protocol):
    async def store(self, path: StoragePath, content: bytes) -> None: ...
    async def retrieve(self, path: StoragePath) -> bytes: ...
    async def delete(self, path: StoragePath) -> None: ...
```

## 5. Anti-Corruption Layer — Adapter dla Systemu Zewnętrznego

ACL to specjalny adapter, który chroni domenę przed modelem zewnętrznego systemu.

## 6. Testowanie Adapterów

Adaptery testujemy przez **integrację** (z prawdziwym zasobem) i **jednostkowo** (z mockiem portu).

```python
# Test integracyjny adaptera
@pytest.mark.integration
class TestSqlExecutionRepository:
    async def test_add_and_get(self, db_session: AsyncSession) -> None:
        repo = SqlExecutionRepository(db_session, ExecutionMapper())
        execution = ExecutionFactory.create()
        await repo.save(execution)
        await db_session.flush()
        result = await repo.get(execution.id)
        assert result.id == execution.id

# Test jednostkowy z mockiem portu
class TestCreateExecutionHandler:
    async def test_uses_clock(self) -> None:
        fixed_time = Timestamp.from_iso("2025-01-01T00:00:00Z")
        clock = Mock(spec=Clock)
        clock.now.return_value = fixed_time
        
        handler = CreateExecutionHandler(
            repo=InMemoryExecutionRepository(),
            factory=ExecutionFactory(UuidIdGenerator(), clock),
            ...
        )
```

## 7. Ewolucja Portu

Port ewoluuje — dodawanie nowych metod jest bezpieczne. Usuwanie/zmiana wymaga koordynacji.

```python
# Wersja 1
class FileStorage(Protocol):
    async def store(self, path: str, content: bytes) -> None: ...
    async def retrieve(self, path: str) -> bytes: ...

# Wersja 2 — dodanie metody (bezpieczne)
class FileStorage(Protocol):
    async def store(self, path: str, content: bytes) -> None: ...
    async def retrieve(self, path: str) -> bytes: ...
    async def delete(self, path: str) -> None: ...  # Nowa metoda
```

## 8. Lokalizacja

```
# Porty
shell/platform/domain/ports/                        # Uniwersalne porty platformy (Clock, IdGenerator)
shell/<service>/application/<bc>/<aggregate>/ports/                       # Porty aplikacyjne

# Adaptery
shell/platform/infrastructure/time/                 # Adaptery uniwersalne (zegar)
shell/platform/infrastructure/identity/             # Adaptery uniwersalne (IdGenerator)
shell/<service>/infrastructure/<bc>/http/                     # HTTP adaptery
shell/<service>/infrastructure/<bc>/acl/                      # Anti-Corruption Layer
```

Porty wyjściowe konkretnego agregatu (katalogi `repositories/` i `ports/`) i ich
adaptery opisują dedykowane wzorce: Repository, Aggregate Provider i Command Port.

## 9. Podsumowanie — Checklista

Projektując Port & Adapter:
- [ ] Port w domenie (lub aplikacji) — należy do potrzebującego
- [ ] Adapter w infrastrukturze — implementuje kontrakt
- [ ] Adapter testowany integracyjnie
- [ ] Domenowy kod używający portu testowany z mockiem/InMemory
