# AI Developer Instructions — Projekt shell

Te instrukcje obowiązują przy **każdym zadaniu, refaktoryzacji i rozbudowie kodu** w tym repozytorium. Ich nadrzędnym celem jest ochrona Czystej Architektury (Clean Architecture) i zasad DDD przed erozją. Jedynym źródłem prawdy dla struktury i zachowań systemu jest kod produkcyjny oraz testy zawarte w `shell/`.

## Topologia i Struktura Projektu

Cały kod produkcyjny oraz testowy systemu znajduje się w katalogu `shell/`. Projekt jest zaprojektowany jako jeden spójny kontekst biznesowy (Single Bounded Context) z jawnym podziałem na warstwy architektury czystej.

shell/                  # Główny i jedyny katalog aplikacji
├── domain/                 # Czysta logika biznesowa, encje, Value Objects
├── application/            # Przypadki użycia: Commands, Queries, Handlers, Porty
├── infrastructure/         # Adaptery systemowe: persistence (SQL/Mongo), FS, messaging
├── framework/              # Interfejsy wejściowe: HTTP (FastAPI), CLI (argparse)
├── bootstrap/              # Fabryka aplikacji i ręczne składanie zależności (DI)
├── shared/                 # Generyczne, niezwiązane z domeną helpery techniczne
└── tests/                  # Architektura testowa (unit, integration, e2e, architecture)
workplace/                  # Notatki, dumpy kontekstu, przykłady zadań (read-only)


**Reguła #1:** Wszystkie nowe funkcjonalności, modyfikacje oraz refaktoryzacje mogą być wprowadzane **wyłącznie** wewnątrz struktury warstwowej `shell/`. Tworzenie jakichkolwiek plików, skryptów czy katalogów w katalogu głównym repozytorium (poza `shell/`) jest zabronione.

**Reguła #2:** Każda warstwa w `shell/` ma ściśle określoną odpowiedzialność. Niedopuszczalne jest mieszanie odpowiedzialności (np. umieszczanie logiki biznesowej w `framework/` lub definicji tabel bazodanowych w `domain/`). Każdy komponent musi trafić do swojej dedykowanej podwarstwy.

## Cykl Pracy Nad Zadaniem (Workflow)

Każde nowe wymaganie biznesowe, modyfikacja czy refaktoryzacja w systemie `shell` musi być wdrażana według ścisłego, warstwowego cyklu. Pracę prowadzimy od wnętrza architektury na zewnątrz (Inside-Out).

1. **Analiza Domenowa i Definicja Kontraktu:** Zanim powstanie jakikolwiek kod infrastruktury (baza danych, API), zdefiniuj encje, Value Objects lub reguły biznesowe w warstwie `domain/`. Jeśli zadanie realizuje przypadek użycia, stwórz niezmienny kontrakt wejściowy w `application/` w postaci `@dataclass(frozen=True)` jako `*Command` lub `*Query`.

2. **Ścisła Kolejność Warstw (Rygor Architektoniczny):**
   Kod implementujemy wyłącznie w kolejności od warstw niezależnych do zależnych:
   `domain` → `application` (Porty i Handlery) →[ `infrastructure` (Adaptery/Repozytoria) & `framework` (API/CLI) ] → `bootstrap` (Spięcie w kontenerze).

[ framework (API/CLI) ] ──┐
│
▼
[ domain ] ◄─── [ application (Use Cases/Ports) ]
▲
│
[ infrastructure (SQL) ] ───┘
▲
│
─────── [ bootstrap ] ───────


   *Zasada bezwzględna:* Nie piszemy kodu wyższej warstwy (np. endpointu w FastAPI), dopóki warstwy niższe (domena, porty, handlery) nie są w pełni zaimplementowane i przetestowane.

3. **Równoległe Testowanie (Co-iterative Testing):**
   Kod produkcyjny i testy powstają w tej samej iteracji. Obowiązuje zasada: **Zero kodu produkcyjnego bez odpowiadającego mu testu**.
   - Modyfikacja logiki w `domain/` lub `application/` = natychmiastowy test jednostkowy (unit test) bez I/O i bez zewnętrznych mocków.
   - Modyfikacja/dodanie adaptera w `infrastructure/` = test integracyjny na realnym komponencie (baza danych, system plików).
   - Zmiany w endpointach/CLI we `framework/` = testy End-to-End (E2E).

4. **Kompilacja i Weryfikacja Lokalna:**
   Zadanie uznaje się za ukończone w rozwoju lokalnym dopiero wtedy, gdy cały lokalny pipeline weryfikacji (Linter, Typowanie, Testy Architektoniczne AST oraz Testy Integracyjne) zwraca status zielony przed wypchnięciem kodu do repozytorium.

## Reguły Warstw (Twarde Strażniki Architektury — Łamanie = Błąd Krytyczny)

Wszystkie komponenty w `shell/` muszą ściśle przestrzegać izolacji warstwowej. Kierunek zależności i dozwolonych importów jest wyłącznie jednostronny i biegnie od zewnątrz do wewnątrz:

domain ← application ← infrastructure ← framework ← bootstrap

Importy w kierunku przeciwnym lub pomijające sąsiednie warstwy są natychmiast odrzucane przez skaner architektoniczny.



### 1. Warstwa Domu (domain/) — Pure Python
* **Odpowiedzialność:** Logika biznesowa, reguły niezmiennicze (invariants), encje, Value Objects, wyjątki domenowe (`DomainError`).
* **Dozwolone importy:** Wyłącznie biblioteka standardowa Pythona (np. `dataclasses`, `enum`, `typing`, `datetime`, `uuid`, `hashlib`).
* **Bezwzględny zakaz:** Zakaz importowania czegokolwiek z `application/`, `infrastructure/`, `framework/` lub `bootstrap/`.
* **Zakaz bibliotek zewnętrznych:** Całkowity brak zależności od frameworków I/O i zewnętrznych: `sqlalchemy`, `pydantic`, `fastapi`, `motor`. 
* *Wyjątek dla ścieżek:* Zakaz używania `pathlib.Path` wewnątrz struktur domenowych. Jeśli encja potrzebuje operować na ścieżce roboczej, musi ona być opakowana w Value Object (np. `WorkspacePath`) jako zwykły, nieprzejrzysty ciąg znaków (`opaque str`).

### 2. Warstwa Aplikacji (application/) — Przypadki Użycia (Use Cases)
* **Odpowiedzialność:** Orkiestracja przypadków użycia, definicja komend/zapytań (`*Command`, `*Query`) oraz ich handlerów (`*Handler`). Definiuje **Porty** (`typing.Protocol`), czyli interfejsy dla świata zewnętrznego (np. repozytoria, loggery, loadery).
* **Dozwolone importy:** Może importować wyłącznie z warstwy `domain/`.
* **Bezwzględny zakaz:** Zakaz importowania jakichkolwiek klas implementacyjnych (adapterów) z `infrastructure/`, `framework/` lub `bootstrap/`. Handlery mogą komunikować się z bazą danych czy systemem plików **wyłącznie przez abstrakcyjne porty (interfejsy)** wstrzykiwane przez konstruktor.
* **Asynchroniczność:** Wszystkie metody portów i handlerów muszą być bezwzględnie asynchroniczne (`async def`).

### 3. Warstwa Infrastruktury (infrastructure/) — Adaptery Techniczne
* **Odpowiedzialność:** Techniczna realizacja portów zdefiniowanych w warstwie aplikacji i domenie. Tutaj znajdują się konkretne repozytoria bazy danych (`SqlAlchemy`, `Motor/Mongo`), integracje z systemem plików (`pathlib`), systemy logowania czy wysyłki zdarzeń.
* **Dozwolone importy:** Może swobodnie importować z warstw `domain/` oraz `application/`.
* **Bezwzględny zakaz:** Zakaz importowania czegokolwiek z warstw wyższych: `framework/` oraz `bootstrap/`. Warstwa techniczna nie może wiedzieć, czy aplikacja jest uruchamiana przez API HTTP, czy przez konsolę CLI.

### 4. Warstwa Frameworku (framework/) — Punkty Wejścia (Driving Adapters)
* **Odpowiedzialność:** Obsługa interfejsów wejściowych systemu: CLI (`argparse`) oraz API HTTP (`FastAPI`). Odpowiada wyłącznie za: odebranie i zwalidowanie żądania (np. Pydantic w FastAPI) -> zmapowanie danych na czysty obiekt `Command`/`Query` -> przesłanie go do szyny (`await bus.dispatch(cmd)`) -> zwrócenie surowego wyniku lub zmapowanie błędu domenowego na status HTTP.
* **Logika:** **Całkowite zero logiki biznesowej ani aplikacyjnej.** Warstwa frameworku pełni jedynie rolę tłumacza sygnałów zewnętrznych na komendy zrozumiałe dla aplikacji.
* **Bezwzględny zakaz:** Zakaz importowania bezpośrednich handlerów aplikacyjnych lub kodu z `bootstrap/`. Komunikacja z aplikacją odbywa się wyłącznie za pośrednictwem szyn (`CommandBus`, `QueryBus`).

### 5. Warstwa Bootstrapu (bootstrap/) — Kompozytor Systemu
* **Odpowiedzialność:** Ręczna konfiguracja kontenera zależności (`Container`) oraz fabryki aplikacji (`ApplicationFactory`). To tutaj wczytywane są zmienne środowiskowe, tworzone są fabryki sesji bazodanowych, instancjonowane są konkretne adaptery z `infrastructure/` i wstrzykiwane do odpowiednich handlerów w `application/`. Na koniec rejestruje gotowe handlery w szynach aplikacyjnych.

---

## Automatyczna Weryfikacja Architektoniczna

Zasada czystości importów nie jest tylko zapisem tekstowym — jest bezwzględnie egzekwowana programistycznie.

* **Strażnik AST:** Plik `shell/tests/architecture/test_imports.py` zawiera automatyczny skaner drzewa składniowego (AST). Sprawdza on każdy plik w projekcie pod kątem niedozwolonych importów wstecznych.
* **Uruchamianie:** Test architektoniczny jest wykonywany w każdym lokalnym potoku testowym (`pytest shell/tests -x`) oraz w procesie CI/CD. Złamanie dowolnej z powyższych zasad warstw skutkuje natychmiastowym wyłożeniem się testów i odrzuceniem kodu.

Markdown
## Konwencje Kodu i Standardy Implementacji

Wszystkie pliki źródłowe w katalogu `shell/` muszą być zgodne z poniższymi standardami programistycznymi. Konwencje te są egzekwowane przez linter oraz statyczną analizę typów.

### 1. Podstawy Językowe i Asynchroniczność
- **Wersja:** Python 3.11+.
- **Typowanie:** Każdy plik zawierający podpowiedzi typów (type hints) musi zaczynać się od obowiązkowej dyrektywy na samym początku pliku:
  ```python
  from __future__ import annotations
Asynchroniczność: Wszystkie metody w portach (application/ports/) oraz wszystkie handlery przypadków użycia muszą być bezwzględnie asynchroniczne (async def). Zabrania się mieszania kodu synchronicznego i asynchronicznego w warstwie aplikacji.

2. Modelowanie Danych (Data Modeling)
Value Objects oraz Komendy/Zapytania (CQRS): Muszą być niezmienne. Definiujemy je wyłącznie jako:

Python
@dataclass(frozen=True, slots=True)
Ewentualna walidacja spójności danych (invariants) musi odbywać się w metodzie __post_init__.

Encje domenowe (Mutable Entities): Obiekty posiadające własną tożsamość, których stan może ulegać zmianie, definiujemy jako:

Python
@dataclass(slots=True)
Porty (Abstrakcje): Definiowane za pomocą typing.Protocol. Dekoratora @runtime_checkable używamy tylko wtedy, gdy walidacja typu w locie (isinstance) jest absolutnie niezbędna. Preferujemy elastyczne struktury typu duck typing.

DTO / Konfiguracja / Modele Requestów: Do walidacji danych wejściowych na brzegu aplikacji (warstwa framework/ dla FastAPI) używamy wyłącznie Pydantic v2 (BaseModel, BaseSettings).

3. Bezwzględne Zakazy Projektowe (Antywzorce)
Zabrania się wprowadzania do kodu shell następujących mechanizmów (naruszenie skutkuje odrzuceniem kodu):

Zakaz sztucznych właściwości: NIE używamy konwencji prywatnych slotów połączonych z publicznymi property z podkreśleniem na końcu (np. slot _name + property name_). Stosujemy bezpośredni, czysty dostęp do pól dataclass dla **Value Objects, Commands, Queries, Domain Events, DTO oraz BaseSettings**.

Wyjątek (DDD primitives): klasy dziedziczące po `shell.domain.entities.base.Entity` lub `shell.domain.entities.base.AggregateRoot` są pisane jako jawne klasy z `__slots__` (NIE jako dataclass) i używają wzorca prywatne pole `_pole` + publiczne `@property pole`. Wynika to z natury encji DDD: tożsamość niezmienna po konstrukcji, stan pól mutowalny TYLKO przez metody domenowe wyrażające reguły biznesowe (np. `task.supersede()`, `workflow.start()`). Bezpośredni publiczny dostęp do pól dataclass byłby tutaj antywzorcem (encja straciłaby kontrolę nad swoimi inwariantami). Wzorzec ten dotyczy WYŁĄCZNIE encji i agregatów.

Zakaz rozproszonych plików funkcyjnych: NIE tworzymy katalogów strukturalnych typu internal/_init_*.py czy plików _assert_*.py zawierających pojedyncze funkcje. Kod grupujemy w czytelne moduły domenowe.

Zakaz klas-fasad dla ścieżek: NIE tworzymy własnych klas udających lub zastępujących system plików. W warstwach technicznych używamy bezpośrednio i wyłącznie standardowego pathlib.Path.

Zakaz leniwej inicjalizacji (Lazy Init): Inicjalizacja obiektów i ich zależności musi być jawna i odbywać się w momencie konstruowania obiektu, a nie w ukrytych mechanizmach getterów/property.

Zakaz grubych wrapperów folder-DOM: Zabrania się tworzenia skomplikowanych struktur owijających drzewo katalogów (typu AppNode, Node, SubNode). Reprezentacja struktury zadań musi być lekka i czysto domenowa.

4. Konwencje Nazewnictwa (Naming Conventions)
Moduły (Pliki): Piszemy w snake_case.py. Obowiązuje zasada: jedna główna klasa publiczna (encja/port/handler) na plik.

Commands & Handlers: Komenda to intencja zmiany stanu: *Command (np. ImportTaskCommand). Jej wykonawca to: *Handler (np. ImportTaskHandler).

Queries & Handlers: Zapytanie o dane (tylko odczyt): *Query (np. GetWorkflowQuery). Jej wykonawca to: *Handler (np. GetWorkflowHandler).

Porty Repozytoriów: Zawsze kończą się sufiksem *Repository (np. TaskExecutionRepository).

Adaptery Infrastruktury: Zawsze wskazują na technologię: <Technologia><Nazwa>Repository (np. SqlTaskExecutionRepository, MongoTaskExecutionRepository, InMemoryTaskExecutionRepository).

Unit of Work: Klasy zarządzające transakcjami nazywamy <Technologia}UnitOfWork (np. SqlAlchemyUnitOfWork).

Zdarzenia domenowe (Domain Events): Reprezentują fakt historyczny, dlatego muszą być rzeczownikami w czasie przeszłym: *Event (np. TaskImported, EnvelopeRouted).

5. Obsługa Wyjątków, Logowanie i Operacje I/O
Zarządzanie błędami: Wszystkie błędy biznesowe muszą dziedziczyć po bazowym DomainError w domain/exceptions.py. Warstwa infrastructure/ ma prawo rzucać własne wyjątki techniczne (np. bazodanowe), ale musi je bezwzględnie przechwycić i zmapować na odpowiednie błędy domenowe, zanim opuszczą granicę adaptera.

Logowanie zdarzeń: Całkowity zakaz używania systemowego print(). Logowanie odbywa się wyłącznie przez abstrakcyjny port zdefiniowany w application/ports/logger.py, którego implementacja produkcyjna znajduje się w infrastructure/logging/.

Zarządzanie Ścieżkami (FS): Bezpośrednie operacje na plikach i katalogach za pomocą pathlib.Path mogą być wykonywane wyłącznie wewnątrz dedykowanych adapterów w infrastructure/filesystem/.

## Strategia i Architektura Testów

W systemie `shell` testy automatyczne są integralną częścią kodu produkcyjnego. Obowiązuje rygorystyczna piramida testów zapewniająca pełną izolację warstwową.

### 1. Środowisko i Framework
- **Główny zestaw:** `pytest` + `pytest-asyncio`.
- **Konfiguracja:** Zgoda z globalną flagą `asyncio_mode = "auto"` zdefiniowaną w `pyproject.toml`. Wszystkie testy asynchroniczne są automatycznie wykrywane i uruchamiane w pętli zdarzeń (event loop).

### 2. Typy i Lokalizacja Testów (Ścisła Izolacja)
- **`shell/tests/unit/domain/` — Testy Jednostkowe Domeny:**
  Testują czystą logikę biznesową i reguły encji/Value Objects. **Całkowity zakaz operacji I/O, dostępu do sieci czy systemów plików.** Nie używamy tu mocków ani dublerów portów aplikacji – domena jest testowana jako czysty Python (Pure Python).
- **`shell/tests/unit/application/` — Testy Jednostkowe Aplikacji:**
  Testują handlery przypadków użycia (`*Handler`). Wszelkie zależności infrastrukturalne są wstrzykiwane w postaci szybkich dublerów in-memory (`InMemory*` adaptery) oraz obiektów kontrolowanych stanu (`FakeClock`, `FakeIdGenerator`, `FakeNodeExecutionProcessRunner`).
- **`shell/tests/integration/` — Testy Integracyjne:**
  Weryfikują poprawność działania realnych adapterów z warstwy infrastruktury. Podzielone na dedykowane katalogi technologiczne:
  - `sql_sqlite/` oraz `sql_postgres/` — operacje na bazach relacyjnych (SQLAlchemy Async).
  - `mongo/` — operacje na bazie dokumentowej.
  - `process/` — testy integracyjne runnerów systemowych.
  - `filesystem/` — testy fizycznych operacji dyskowych.
  *Zasada środowiskowa:* Testy postgres oraz mongo powinny automatycznie wykrywać brak środowiska docker-compose i nakładać dekorator `@pytest.mark.skipif`.
- **`shell/tests/e2e/` — Testy End-to-End (Pełny Stack):**
  Testują kompletną aplikację od zewnętrznego punktu wejścia aż po stan w bazie danych. Podzielone na testy interfejsu konsolowego (`cli/`) oraz API sieciowego (`api/`).
- **`shell/tests/architecture/` — Testy Architektoniczne:**
  Statyczna weryfikacja poprawności importów za pomocą skanera drzewa AST oraz lintera testów. Zapobiega wyciekom zależności między warstwami.

### 3. Wymagane Wskaźniki Pokrycia (Coverage Targets)
Każda zmiana w kodzie musi utrzymywać lub podnosić minimalne progi pokrycia kodu testami:
- **Warstwa Domeny (`domain/`):** ≥ 90%
- **Warstwa Aplikacji (`application/`):** ≥ 85%
- **Warstwa Infrastruktury (`infrastructure/`):** ≥ 70%

### 4. Konwencje i Obowiązkowa Matryca Scenariuszy
- **Nazewnictwo:** Pliki testowe nazywamy wg schematu `test_<komponent>_<scenariusz>.py` lub strukturyzujemy wewnątrz klas testowych: `test_<komponent>.py::TestKomponent::test_<scenariusz>`.
- **Zasada Nowego Przypadku Użycia:** Każdy nowo dodany lub modyfikowany kontrakt `*Command` lub `*Query` musi posiadać w tej samej iteracji zestaw testów jednostkowych/aplikacyjnych pokrywających **co najmniej 4 obowiązkowe scenariusze**:
  1. **Happy Path:** Sukces wykonania operacji przy poprawnych danych wejściowych.
  2. **Not Found / Missing Record:** Poprawne zachowanie systemu i rzucenie dedykowanego `DomainError` w przypadku braku żądanego rekordu w bazie danych.
  3. **Input Validation:** Próba przekazania nieprawidłowych danych (weryfikacja wyjątków walidacyjnych w `__post_init__` lub warstwie brzegu).
  4. **Transactional Behavior (Dla Komend Zapisujących):** Test sprawdzający poprawne wykonanie `commit()` w przypadku sukcesu oraz automatyczny `rollback()` przy wystąpieniu błędu, realizowany za pomocą asynchronicznego menedżera kontekstu `InMemoryUnitOfWork`.

## Kontrakty i Cykl Życia Szyny Aplikacyjnej (Commands, Queries, Events)

Komunikacja z warstwą aplikacji (`application/`) odbywa się wyłącznie za pośrednictwem dedykowanych szyn komunikatów (`CommandBus`, `QueryBus`, `EventBus`). Każdy komunikat i obsługujący go handler musi spełniać ścisły kontrakt architektoniczny.

### 1. Niezmienność Komunikatów (Immutability)
Wszystkie obiekty intencji (Commands oraz Queries) są czystymi strukturami danych niosącymi parametry wejściowe przypadku użycia. Muszą być całkowicie niezmienne i zoptymalizowane pamięciowo:
```python
@dataclass(frozen=True, slots=True)
class XCommand: ...
2. Anatomia Handlera Aplikacyjnego
Jedna odpowiedzialność: Każdy handler obsługuje dokładnie jeden komunikat i posiada tylko jedną publiczną metodę wykonawczą: async def handle(self, cmd: XCommand) -> Result | None.

Wstrzykiwanie zależności (Constructor Injection): Handler otrzymuje wszystkie niezbędne komponenty wyłącznie przez konstruktor (__init__).

Czystość importów: Wykonawca przypadku użycia nie ma prawa importować konkretnych adapterów z warstwy infrastruktury (np. SqlAlchemyUnitOfWork). Wszystkie zależności w sygnaturze konstruktory muszą być abstrakcyjnymi portami (interfejsami/protokołami).

3. Transakcyjność i Emisja Zdarzeń Domenowych
Zapis lub modyfikacja stanu systemu musi być bezwzględnie atomowa i zabezpieczona transakcyjnie przez asynchroniczny menedżer kontekstu Unit of Work (uow).

Zasada bezpiecznego zapisu: Zmiany na repozytoriach są zatwierdzane jawnie przez await uow.commit(). W przypadku wystąpienia jakiegokolwiek błędu wewnątrz bloku async with, metoda __aexit__ obiektu UoW musi automatycznie wykonać operację rollback.

Izolacja efektów ubocznych (Domain Events): Zdarzenia domenowe (Domain Events) mogą zostać opublikowane przez EventPublisher wyłącznie po pomyślnym zakończeniu transakcji i wyjściu z bloku UoW. Publikacja zdarzeń przed wykonaniem uow.commit() jest błędem krytycznym (mogłoby to doprowadzić do wyemitowania zdarzenia w świat mimo wycofania zmian w bazie danych).

4. Wzorzec Referencyjny Handlera (Python 3.11+)
Każdy nowo implementowany handler aplikacyjny musi strukturalnie odpowiadać poniższemu wzorcowi:

Python
from __future__ import annotations
from dataclasses import dataclass
from shell.domain.entities.task import Task
from shell.domain.events.task import TaskImported
from shell.domain.value_objects.id import TaskId
from shell.application.ports.ports import (
    UnitOfWork, 
    Clock, 
    IdGenerator, 
    TaskLoader, 
    EventPublisher
)

@dataclass(frozen=True, slots=True)
class ImportTaskCommand:
    name: str
    md_path: str
    yaml_path: str

class ImportTaskHandler:
    def __init__(
        self, 
        uow: UnitOfWork, 
        clock: Clock, 
        id_gen: IdGenerator,
        task_loader: TaskLoader, 
        events: EventPublisher
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._task_loader = task_loader
        self._events = events

    async def handle(self, cmd: ImportTaskCommand) -> TaskId:
        # 1. Odczyt zewnętrznych danych wejściowych przez abstrakcyjny port
        body_md, body_yaml = await self._task_loader.load(cmd.md_path, cmd.yaml_path)
        
        # 2. Tworzenie nowej encji/agregatu wewnątrz czystej domeny
        task_id = self._id_gen.new_task_id()
        task = Task.new(
            id_=task_id,
            name=cmd.name, 
            body_md=body_md, 
            body_yaml=body_yaml,
            created_at=self._clock.now()
        )
        
        # 3. Transakcyjny zapis stanu agregatu w bazie danych
        async with self._uow as uow:
            await uow.tasks.save(task)
            await uow.commit()  # Jawny commit na końcu bloku sukcesu
            
        # 4. Bezpieczna publikacja zdarzeń po utrwaleniu transakcji
        await self._events.publish([TaskImported(task_id=task.id, name=task.name)])
        
        return task_id

---

## Strategia Utrwalania Danych (Persistence — Spójność 2 Adapterów)

System `shell` opiera się na strategii dwóch równorzędnych mechanizmów trwałości danych (Persistence). Każdy port repozytorium zdefiniowany w domenie lub aplikacji musi posiadać dokładnie dwie kompletne implementacje infrastrukturalne.

### 1. Relacyjne Bazy Danych (SQL: SQLite + PostgreSQL)
- **Lokalizacja kodu:** `shell/infrastructure/persistence/sql/`
- **Technologia:** SQLAlchemy 2.x w trybie w pełni asynchronicznym (`AsyncSession`).
- **Zasada współdzielenia:** SQLite (używany lokalnie w szybkich testach integracyjnych) oraz PostgreSQL (używany produkcyjnie) współdzielą tę samą warstwę mapowania ORM oraz te same klasy repozytoriów.
- **Różnice dialektów:** Różnice między bazami mogą dotyczyć wyłącznie fabryki sesji (`session_factory` w bootstrapie) oraz specyficznych typów kolumn (np. mapowanie generycznego pola JSON na natywny typ `JSON` w SQLite vs `JSONB` w PostgreSQL) na poziomie migracji.

### 2. Implementacja Pamięciowa (InMemory)
- **Lokalizacja kodu:** `shell/infrastructure/persistence/memory/`
- **Zasada działania:** Szybkie repozytoria i Unit of Work realizujące stan w czystej pamięci operacyjnej procesu (za pomocą natywnych słowników Pythona).
- **Przeznaczenie:** Ta warstwa służy wyłącznie do błyskawicznego wykonywania testów jednostkowych warstwy aplikacji (`shell/tests/unit/application/`), całkowicie eliminując potrzebę dotykania dysku czy kontenerów podczas testów Use Case'ów.

### 3. Bezwzględna Reguła Duetu Repozytoriów
Wprowadzenie jakiejkolwiek zmiany w warstwie persystencji podlega zasadzie „wszystko albo nic”:
- **Zasada rozszerzania:** Dodanie nowego portu repozytorium lub rozszerzenie istniejącego o nową metodę (np. dodanie `find_by_status` do `TaskExecutionRepository`) wymaga **natychmiastowej i jednoczesnej** implementacji tej metody w dwóch klasach adapterów: `Sql*Repository` oraz `InMemory*Repository`.
- **Wymóg testowy:** Oba adaptery oraz powiązany z nimi `UnitOfWork` muszą posiadać dedykowane testy (odpowiednio: integracyjne dla SQL i jednostkowe dla aplikacji korzystające z wersji InMemory).

### 4. Zarządzanie Migracjami Schematów
Ewolucja struktur danych w bazie danych jest w 100% relacyjna i kontrolowana centralnie:
- **Narzędzie:** Wszystkie migracje są zarządzane wyłącznie przez framework `Alembic`.
- **Lokalizacja:** Pliki migracji i wersje schematów muszą znajdować się w katalogu `shell/infrastructure/persistence/migrations/sql/versions/`.

## Interfejsy Wejściowe (Warstwa Framework: CLI & API)

Warstwa `framework/` odpowiada wyłącznie za obsługę punktów wejścia do aplikacji. Jej jedynym zadaniem jest przyjęcie zewnętrznych danych, transformacja ich w obiekt `Command` lub `Query`, przesłanie do odpowiedniej szyny aplikacyjnej i zwrócenie wyniku.

### 1. Interfejs Konsolowy (CLI)
- **Technologia:** Używamy wyłącznie wbudowanej biblioteki standardowej Pythona `argparse`. Zabrania się wprowadzania zewnętrznych frameworków CLI (np. `Typer`, `Click`).
- **Struktura komend:** Główny punkt wejścia konsoli zarządza dedykowanymi podkomendami (Subcommands): `agent`, `router`, `tasker`, `tool`, `worker`, `import-task`, `workflow`, `route`.
- **Lokalizacja i wzorzec:** Oficjalne punkty wejścia znajdują się w `shell/framework/entrypoints/`. Odpowiadają one za sparsowanie tablicy `sys.argv`, pobranie instancji kontenera z bootstrapu i przekazanie intencji do szyny. Zero logiki warunkowej wewnątrz parserów.

### 2. Interfejs Sieciowy (HTTP API)
- **Technologia:** `FastAPI` w trybie asynchronicznym.
- **Inicjalizacja aplikacji:** Cała aplikacja webowa jest tworzona za pomocą wzorca fabryki: pojedynczej funkcji `create_app(container: Container) -> FastAPI` zlokalizowanej w `shell/framework/api/app.py`. Kontener zależności z warstwy bootstrapu musi być jawnie przekazany podczas startu serwera.
- **Wstrzykiwanie Zależności (DI):** Endpointy (routery) FastAPI nie mogą bezpośrednio instancjonować ani importować adapterów infrastruktury. Dostęp do szyn aplikacyjnych lub globalnych usług uzyskują wyłącznie poprzez mechanizm FastAPI `Depends`, pobierając gotowy obiekt z kontenera (np. `Depends(get_container)`).

### 3. Globalne Mechanizmy Middleware i Obserwowalność
Brzeg systemu HTTP jest zabezpieczony dwoma obowiązkowymi komponentami middleware:
- **Identyfikacja Żądań (`correlation_id`):** Każde żądanie HTTP musi automatycznie generować lub przekazywać dalej unikalny identyfikator korelacji, zarządzany za pomocą `contextvars`. Identyfikator ten musi być automatycznie dołączany do każdego wpisu w logach w celu pełnego śledzenia rozproszonego (tracing).
- **Globalna Obsługa Błędów (`error_handler`):** Centralny interceptor wyjątków. Odpowiada za przechwytywanie wszelkich błędów dziedziczących po `DomainError`. Logika biznesowa nie powinna przejmować się statusami HTTP – middleware automatycznie mapuje błędy domenowe na odpowiednie statusy z rodziny 4xx (np. `TaskNotFoundError` -> `HTTP 404`). Niewychwycone błędy techniczne (np. awaria bazy) są mapowane na bezpieczne `HTTP 500`.

## Definition of Done (DoD — Kryteria Ukończenia Zadania)

Zgłoszenie zmian (Pull Request) lub zadanie deweloperskie uznaje się za ukończone i gotowe do wdrożenia na produkcję wyłącznie wtedy, gdy spełnia 100% poniższych kryteriów weryfikacji automatycznej i architektonicznej.

### 1. Zgodność Architektoniczna i Izolacja Warstw
- Kod został umieszczony w prawidłowych katalogach odpowiadających warstwom architektury.
- Test architektoniczny oparty na skanerze AST (`pytest shell/tests/architecture/test_imports.py`) przechodzi pomyślnie, potwierdzając brak niedozwolonych importów wstecznych.

### 2. Kompletność i Zielony Status Testów
- Wszystkie testy automatyczne (jednostkowe, integracyjne oraz E2E) wykonują się pomyślnie i zwracają status zielony.
- Dla każdego nowego lub modyfikowanego przypadku użycia dodano testy pokrywające obowiązkową matrycę 4 scenariuszy (Happy Path, Not Found, Input Validation, Transactional Behavior).
- Zmiany nie powodują regresji – globalny wskaźnik pokrycia kodu (Coverage) nie spadł poniżej wymaganych progów (Domain ≥90%, Application ≥85%, Infrastructure ≥70%).

### 3. Statyczna Analiza Jakości Kodu (Ruff)
- Kod przeszedł pomyślnie weryfikację lintera oraz formatera. Narzędzie `ruff` nie zwraca żadnych błędów ani ostrzeżeń:
  ```bash
  ruff check shell
4. Rygorystyczna Kontrola Typowania (Mypy)
Warstwy rdzenia biznesowego aplikacji muszą być w 100% bezpieczne pod kątem typów. Kontrola typów w trybie --strict musi przechodzić bezbłędnie:

Bash
mypy --strict shell/domain shell/application
Warstwy zewnętrzne systemu (infrastructure oraz framework) muszą pomyślnie przechodzić standardową weryfikację typów (bez flagi --strict).

5. Czystość Środowiska i Pracy z Bazą Danych
Jeśli zadanie wymagało modyfikacji schematu bazy danych SQL, w katalogu migracji wygenerowano i pomyślnie przetestowano nowy plik migracyjny Alembic.

Zmiany zostały zaimplementowane w pełnym duecie repozytoriów (Sql* oraz InMemory*). Żaden port nie został pozostawiony bez działającej implementacji pamięciowej do testów.

---

## Bezwzględne Antywzorce i Zakazy (Czego NIE Robić)

Poniższa lista określa praktyki programistyczne, które są kategorycznie zabronione w repozytorium `shell`. Wprowadzenie którejkolwiek z nich skutkuje natychmiastowym odrzuceniem kodu w procesie review.

### 1. Zakaz Automatycznych i Zewnętrznych Frameworków DI
- **Reguła:** Obowiązuje bezwzględny zakaz wprowadzania i używania zewnętrznych kontenerów lub frameworków do wstrzykiwania zależności (takich jak `dependency-injector`, `punq`, `lagom`, `injector` itp.).
- **Rozwiązanie docelowe:** Cały graf zależności systemu musi być budowany w sposób jawny, czytelny i w 100% kompilowalny przez interpreter Pythona (tzw. **Pure DI / Ręczne wstrzykiwanie zależności**). Za składanie komponentów odpowiada wyłącznie `ApplicationFactory` oraz klasa `Container` zlokalizowana w warstwie `bootstrap/`.

### 2. Ścisła Kontrola Zależności Zewnętrznych
- **Reguła:** Zabrania się samowolnego dodawania nowych bibliotek i pakietów do pliku konfiguracji środowiska (`pyproject.toml` / `poetry` / `pipenv`).
- **Uzasadnienie:** Rdzeń aplikacji oraz logika biznesowa muszą pozostać maksymalnie niezależne od zewnętrznego ekosystemu, co gwarantuje łatwość aktualizacji Pythona i stabilność długoterminową. Każda nowa biblioteka wymaga wcześniejszej akceptacji architektonicznej.

### 3. Zakaz Zanieczyszczania Repozytorium Dokumentacją Tymczasową
- **Reguła:** Nie twórz luźnych plików tekstowych ani markdownów dokumentujących bieżące zmiany w kodzie, changelogów wewnątrz katalogów roboczych czy lokalnych notatek deweloperskich (chyba że zostaniesz o to wprost poproszony).
- **Rozwiązanie docelowe:** Jedynym źródłem prawdy o działaniu systemu jest czysty kod oraz intencje biznesowe wyrażone w testach. Trwałe decyzje architektoniczne mogą być dokumentowane wyłącznie jako sformalizowane pliki ADR (Architecture Decision Records) w wyznaczonym do tego katalogu, jeśli wymaga tego struktura governance projektu.

### 4. Zakaz Ukrywania Efektów Ubocznych i Mieszania Paradygmatów I/O
- **Zakaz używania `print()`:** Całkowity ban na instrukcje `print()`. Monitorowanie aplikacji i diagnostyka błędów mogą odbywać się wyłącznie za pośrednictwem abstrakcyjnego portu loggera wstrzykiwanego do komponentów.
- **Zakaz mieszania Sync/Async:** Niedopuszczalne jest blokowanie asynchronicznej pętli zdarzeń (event loop) poprzez wywoływanie synchronicznych, blokujących funkcji I/O (np. standardowe `open()`, synchroniczne zapytania HTTP) wewnątrz asynchronicznych handlerów czy portów aplikacji. Warstwa aplikacyjna musi zachować 100% spójność asynchroniczną.

---

## Szybka Weryfikacja Lokalna (Środowisko PowerShell / Windows)

Poniższe skróty klawiszowe i komendy służą do szybkiego uruchamiania testów oraz statycznej analizy kodu w lokalnym środowisku deweloperskim. Każda z tych komend musi zwracać status zielony przed wypchnięciem kodu.

### 1. Uruchamianie Testów (Pytest)
```pwsh
# Wykonanie wszystkich testów w projekcie (zatrzymanie na pierwszym błędzie)
pytest shell/tests -x

# Uruchomienie wyłącznie szybkich testów jednostkowych (czysta domena i aplikacja)
pytest shell/tests/unit -x

# Błyskawiczne testy integracyjne na lokalnej bazie SQLite (bez podnoszenia Dockera)
pytest shell/tests/integration/sql_sqlite -x
2. Statyczna Analiza Jakości i Kontrola Typów
Fragment kodu
# Szybki lint oraz automatyczne formatowanie kodu
ruff check shell

# Rygorystyczna kontrola typów w rdzeniu biznesowym (Domain & Application)
python -m mypy --strict shell/domain shell/application
3. Pełne Testy Integracyjne (Wymaga Docker Compose)
Fragment kodu
# 1. Podniesienie lokalnej bazy testowej PostgreSQL w tle
docker compose -f shell/docker-compose.test.yml up -d postgres

# 2. Uruchomienie pełnego zestawu testów integracyjnych (SQLite + Postgres + FS)
python -m pytest shell/tests/integration -x

# 3. Bezpieczne zatrzymanie kontenerów wraz z czyszczeniem wolumenów danych
docker compose -f shell/docker-compose.test.yml down -v

---
