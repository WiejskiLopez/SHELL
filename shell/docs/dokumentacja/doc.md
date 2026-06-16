[ Klient / Testy / API ]
│
▼
┌────────────────────────────────────────────────────────┐
│ WARSTWA INFRASTRUKTURY WEJŚCIOWEJ                      │
│ - Tworzy: Command / Query (DTO)                        │
│ - Wywołuje: CommandBus.dispatch() / QueryBus.dispatch()│
└───────────────────────┬────────────────────────────────┘
│
▼
┌────────────────────────────────────────────────────────┐
│ WARSTWA APLIKACJI (Buses & Handlers)                   │
│ - Szyny (CommandBus, QueryBus) przekazują paczkę do:   │
│   -> CommandHandler (np. StartWorkflowHandler)         │
└───────────────────────┬────────────────────────────────┘
│
├──────────────────────────────────────────┐
▼ (używa portów / interfejsów)             ▼ (zapisuje eventy)
┌──────────────────────────────────────────┐   ┌─────────────────────────────────────┐
│ PORTY APLIKACJI (Interfejsy)             │   │ PORT EVENTÓW                        │
│ - UnitOfWork (Abstract)                  │   │ - EventPublisher (Abstract)         │
└───────────────────────┬──────────────────┘   └───────────────────┬─────────────────┘
│                                          │
▼ (konkretna implementacja)                ▼ (konkretna implementacja)
┌──────────────────────────────────────────┐   ┌─────────────────────────────────────┐
│ ADAPTERY INFRASTRUKTURY                  │   │ ADAPTER TRANSMISJI                  │
│ - SqlAlchemyUnitOfWork                   │   │ - SqlOutboxPublisher                │
│   (Zarządza AsyncSession)                │   │   (Zapisuje do OutboxEventModel)    │
│ - SqlPromptRepository, etc.              │   └─────────────────────────────────────┘
└───────────────────────┬──────────────────┘
│
▼ (ładuje / zapisuje)
┌────────────────────────────────────────────────────────┐
│ WARSTWA DOMENY (Jądro systemu)                         │
│ - Agregaty & Encje (Envelope, Prompt, Task)           │
│ - Logika biznesowa, niezmienniki, reguły stanów        │
└────────────────────────────────────────────────────────┘


🔄 Szczegółowy podział na warstwy i relacje klas
1. Wejście do systemu (Infrastruktura aplikacyjna)
   Klasy: TestSqlCommitRollback, StartWorkflowCommand, GetPromptQuery.

Przepływ: Zewnętrzny świat (np. test integracyjny lub kontroler API) tworzy niemutowalny obiekt intencji (Command lub Query) 
i wrzuca go do odpowiedniej szyny (CommandBus/QueryBus).

Zależność: Warstwa ta zależy wyłącznie od interfejsu szyny oraz struktur DTO/Commands.

2. Warstwa Orkiestracji (Aplikacja / Handlery)
   Klasy: CommandBus, QueryBus, StartWorkflowHandler, SaveNodeResultHandler.

Przepływ: CommandBus znajduje w słowniku _handlers odpowiednią klasę handlera i wywołuje metodę handle(command).

Zależność: Handlery implementują logikę aplikacyjną. Nie wykonują operacji na bazie danych bezpośrednio – w swoim konstruktorze 
przyjmują abstrakcję UnitOfWork (Dependency Injection).

3. Warstwa Dostępu do Danych (Adaptery Infrastruktury)
   Klasy: SqlAlchemyUnitOfWork, SqlPromptRepository, SqlEnvelopeRepository.

Przepływ: 1. Handler otwiera kontekst menedżera: async with self._uow as uow:.
2. SqlAlchemyUnitOfWork tworzy sesję SQLAlchemy (AsyncSession).
3. Handler poprzez uow.prompts lub uow.envelopes wywołuje metody repozytorium (np. save(), get_by_id()).

Zależność: Klasy repozytoriów zależą od modeli SQLAlchemy (OutboxEventModel, etc.), ale mapują je na czyste obiekty domenowe.

4. Serce Biznesowe (Czysta Domena)
   Klasy: Envelope, Prompt, Task, TaskId, Status.

Przepływ: Repozytorium wyciąga surowe dane z bazy, rekonstruuje z nich obiekt domenowy (np. Envelope) 
i przekazuje go do Handlera. Handler wywołuje na encji metodę biznesową (np. zmianę stanu, walidację).
Encja modyfikuje swój stan wewnętrzny i opcjonalnie generuje zdarzenie (np. WorkflowStarted).

Zależność: Brak zależności zewnętrznych. Domena stoi na samym dole hierarchii. Klasy takie jak TaskId czy Status to 
Value Objects wykorzystywane przez Encje.

5. Asynchroniczny przepływ zdarzeń (Wzorzec Outbox)
   W Twoim kodzie zastosowano genialne oddzielenie efektów ubocznych za pomocą bazy danych:

Plaintext

[Handler / Domena] ──(Generuje DomainEvent)──> [SqlOutboxPublisher] ──> Zapis w DB (outbox_event)
│
(Asynchroniczny proces)
▼
[Klient końcowy] <── [EventBus] <── [EventPublisher] <── [_OutboxProxy] <── [OutboxRelay]

Krok A: Handler po udanej operacji biznesowej przekazuje zdarzenia domenowe do SqlOutboxPublisher.

Krok B: SqlOutboxPublisher tworzy dedykowaną, krótką sesję DB i zapisuje wiersz w tabeli outbox_event jako 
JSON (dzięki temu nawet jeśli transakcja główna się wycofa, ślad o błędzie lub zdarzeniu technicznym może zostać utrwalony, bądź – przy pełnym UoW – zostanie zatwierdzony razem z domeną).

Krok C: OutboxRelay działa w tle. Cyklicznie odpytuje tabelę OutboxEventModel o nieopublikowane wiersze (published_at.is_(None)). 
Wrapuje je w lekkie obiekty _OutboxProxy i przekazuje do właściwego, pamięciowego EventBus, który powiadamia asynchronicznych odbiorców (Event Handlerów).

💡 Kluczowy wniosek architektoniczny
Wszystkie strzałki zależności kompilacji (kto importuje kogo) skierowane są w stronę domeny. Kod infrastruktury bazy danych 
(sql/models.py) implementuje interfejsy zdefiniowane w domenie/aplikacji. Dzięki temu rozwiązaniu, zmiana bazy danych z SQLite/PostgreSQL
na np. MongoDB wymagałaby jedynie napisania nowego adaptera (klasy implementującej porty repozytoriów), podczas gdy cała logika 
w handlerach i encjach pozostałaby nienaruszona.