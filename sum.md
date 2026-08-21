# Audyt bledow platformy

Data audytu: 2026-08-19

## Zakres i metoda

Audyt obejmuje kod wspolnej platformy w `shell/platform/` oraz testy nalezace
do platformy. Priorytet wynika z wplywu na poprawnosc danych, przetwarzanie
dostaw, start uslugi i bezpieczenstwo operacyjne.

Poziomy:

- **P1 - krytyczny/wysoki**: bledne dane lub utrata podstawowego przeplywu.
- **P2 - sredni**: awaria ograniczonego przeplywu albo niespojne zachowanie
  konfiguracyjne.
- **P3 - niski**: ryzyko operacyjne, luka testowa albo problem organizacji
  testow.

## Bledy potwierdzone

### P1. Deserializacja eventu zwraca zly typ `occurred_at`

- **Plik:** [shell/platform/infrastructure/serialization/event/serializer.py](shell/platform/infrastructure/serialization/event/serializer.py#L46)
- **Symbol:** `DomainEventSerializer.from_payload`
- **Mechanizm:** pole `DomainEvent.occurred_at` ma typ `OccurredAt`, ale kod
  obsluguje je specjalnie i nie konstruuje `OccurredAt`. Przy obecnych
  odroczonych adnotacjach typ pola jest lancuchem, wiec metoda zwraca surowy
  `datetime`. Przy rozwiazanej adnotacji druga galaz tworzy `CreatedAt`.
- **Dowod:** bezposrednia reprodukcja zwrocila `datetime False` dla sprawdzenia
  `isinstance(event.occurred_at, OccurredAt)`.
- **Skutek:** zdeserializowany event narusza kontrakt domenowy. Konsument,
  ktory oczekuje `event.occurred_at.value`, moze zakonczyc obsluge wyjatkiem;
  w inboxie dostawa trafi do retry albo DLQ. Ten sam problem dotyczy wszystkich
  eventow korzystajacych z bazowego pola `DomainEvent`.
- **Porownanie:** [shell/platform/infrastructure/serialization/message/serializer.py](shell/platform/infrastructure/serialization/message/serializer.py#L42)
  rozpoznaje typ przez `get_type_hints` i obsluguje `OccurredAt`.
- **Naprawa:** uzyc rozwiazanych adnotacji i deserializacji zalezne od typu,
  tak jak w serializerze wiadomosci; dla `OccurredAt` wywolac
  `OccurredAt.from_datetime`.
- **Brakujacy test:** jednostkowy round-trip eventu z asercja typu
  `OccurredAt`. Obecny test integracyjny sprawdza status inboxu, ale nie typ
  pola eventu: [shell/tests/platform/integration/sql_sqlite/test_event_inbox_processor_refactored.py](shell/tests/platform/integration/sql_sqlite/test_event_inbox_processor_refactored.py#L89).

### P2. Sekwencyjny inbox moze przerwac cala partie po nieoczekiwanym wyjatku

- **Plik:** [shell/platform/infrastructure/messaging/inbox/inbox_processor_base.py](shell/platform/infrastructure/messaging/inbox/inbox_processor_base.py#L186)
- **Symbol:** `InboxProcessorBase.run_once`
- **Mechanizm:** w trybie sekwencyjnym wywolanie
  `_process_claimed_row(...)` nie jest objete obsluga `Exception`. Tryb
  wspolbiezny ma osobny `try/except` w `_run_one`: [shell/platform/infrastructure/messaging/inbox/inbox_processor_base.py](shell/platform/infrastructure/messaging/inbox/inbox_processor_base.py#L206).
- **Warunek:** `_process_claimed_row` obsluguje bledy handlera, ale przed ta
  sekcja wywoluje walidator i deserializator. `EventDeserializer` i
  `MessageDeserializer` obsluguja tylko `KeyError`, `ValueError` i `TypeError`:
  [shell/platform/infrastructure/serialization/event/deserializer.py](shell/platform/infrastructure/serialization/event/deserializer.py#L38).
  Nieoczekiwany wyjatek, na przyklad z transformacji `PayloadUpcaster`, ucieka
  z `run_once`.
- **Skutek:** worker moze zakonczyc pojedyncze uruchomienie wyjatkiem zamiast
  sklasyfikowac dostawke jako nieudana. Kolejne rekordy z tej partii nie zostana
  obsluzone, a ich lease pozostanie do wygasniecia. Zachowanie rozni sie od
  trybu wspolbieznego.
- **Naprawa:** zastosowac wspolna, rekordowa granice obslugi wyjatkow dla obu
  trybow i zachowac istniejaca klasyfikacje retry/DLQ.
- **Brakujacy test:** sekwencyjny test z upcasterem rzucajacym nieoczekiwany
  wyjatek oraz asercja, ze `run_once` zwraca wynik i nie przerywa obslugi
  pozostalych rekordow.

### P2. Ustawienie `reset_db` z YAML jest ignorowane

- **Plik:** [shell/platform/infrastructure/configuration/shell_config.py](shell/platform/infrastructure/configuration/shell_config.py#L147)
- **Symbol:** `LoadedConfiguration.from_environment`
- **Mechanizm:** metoda odczytuje `SHELL_RESET_DB` do lokalnej zmiennej
  `reset_db`, ale nie odczytuje `merged["reset_db"]` i nie zapisuje do `merged`
  wartosci wynikowej. W rezultacie `ServiceConfig.reset_db` zalezy wylacznie od
  zmiennej srodowiskowej.
- **Dowod:** przy `active_profile: dev` i `reset_db: true` w `default.yaml`,
  bez `SHELL_RESET_DB`, wynik `config.service.reset_db` wynosi `False`.
  Dla `SHELL_RESET_DB=true` obecny kod dziala poprawnie.
- **Skutek:** konfiguracja YAML i konfiguracja przez env maja rozne semantyki;
  wlasciciel srodowiska moze wlaczyc ustawienie w pliku profilu i nie otrzymac
  zadnego bledu ani ostrzezenia.
- **Ocena:** defekt jest potwierdzony jako niespojnosc kontraktu loadera.
  Jesli intencja projektu jest celowe wspieranie `reset_db` tylko przez env,
  wpis nalezy zamienic na jawnie udokumentowane ograniczenie, a nie pozostawiac
  obecnego cichego ignorowania YAML.
- **Naprawa:** ustalic jedna kolejnosc zrodel konfiguracji i dodac test zgodnosci
  YAML/env dla profili `dev` i `prod`.

## Niskie priorytety i problemy testowe

### P3. Testy platformy nie maja pelnej izolacji i nie zbieraja sie bez `aio_pika`

- **Objaw:** `python -m pytest shell/tests/platform -q` zatrzymuje kolekcje na
  pieciu bledach `ModuleNotFoundError: No module named 'aio_pika'`.
- **Przyczyna blokady:** testy platformy i helpery E2E importuja kontenery BC,
  ktore importuja transport RabbitMQ podczas kolekcji, np.
  [shell/tests/platform/unit/test_bc_core_containers.py](shell/tests/platform/unit/test_bc_core_containers.py#L30)
  oraz [shell/platform/infrastructure/messaging/transport/rabbit/rabbit_delivery_transport.py](shell/platform/infrastructure/messaging/transport/rabbit/rabbit_delivery_transport.py#L19).
- **Skutek:** pelny pakiet platformy i testy architektury nie daja sie
  zweryfikowac w aktualnym srodowisku. Jest to przede wszystkim problem
  zaleznosci/izolacji testow, nie potwierdzony blad logiki produkcyjnej.
- **Naprawa:** zapewnic deklarowana zaleznosc `aio_pika` w srodowisku testowym
  albo odroczyc import transportu opcjonalnego; testy platformy powinny uzywac
  fake platformowych i nie importowac BC, zgodnie z topologia testow.

### P3. Brak asercji kontraktu typu w istniejacych testach event inbox

Test [shell/tests/platform/integration/sql_sqlite/test_event_inbox_processor_refactored.py](shell/tests/platform/integration/sql_sqlite/test_event_inbox_processor_refactored.py#L89)
potwierdza oznaczenie dostawy jako `PROCESSED`, ale nie sprawdza, czy obiekt
przekazany do busa ma `occurred_at` typu `OccurredAt`. Pozwala to przejsc testom
mimo potwierdzonego bledu deserializacji.

### P3. Brak jednostkowego testu serializer eventow

W testach platformy istnieje test domenowych wiadomosci, ale nie ma
rownorzednego testu `DomainEventSerializer.from_payload`. Taki test powinien
sprawdzac co najmniej typy `occurred_at`, `schema_version` oraz round-trip
wartosci eventu.

## Wyniki walidacji

- `python -m pytest shell/tests/platform/unit/infrastructure/test_shell_config_contract.py -q` - **9 passed**.
- Testy inbox i serializacji:
  `python -m pytest shell/tests/platform/integration/sql_sqlite/test_event_inbox_processor_refactored.py shell/tests/platform/integration/sql_sqlite/test_event_message_inbox_processors.py -q` - **13 passed**.
- `python -m pytest shell/tests/platform -q` - **zablokowane podczas kolekcji**
  przez brak `aio_pika`; piec bledow importu.
- `python -m pytest shell/tests/architecture -x -q` - **zablokowane podczas
  kolekcji** przez ten sam brak `aio_pika`.

## Kolejnosc napraw

1. Naprawic typ `occurred_at` w deserializacji eventow i dodac test jednostkowy.
2. Ujednolicic granice obslugi wyjatkow inbox w trybie sekwencyjnym i
   wspolbiezym oraz dodac test nieoczekiwanego wyjatku.
3. Ustalic i przetestowac jawny kontrakt zrodla `reset_db`.
4. Naprawic izolacje kolekcji testow platformy i uzupelnic zaleznosc
   `aio_pika`, a nastepnie ponowic pelny pakiet testow.

## Ograniczenia audytu

Raport dokumentuje problemy znalezione i potwierdzone w zakresie
`shell/platform/` przy dostepnych zaleznosciach. Nie uruchamiano `deploy.ps1`,
poniewaz wykonuje pelny pipeline oraz `git commit`. Nie zmieniano kodu
produkcyjnego.