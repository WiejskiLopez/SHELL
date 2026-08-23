# Plan kanałów komunikacji SHELL: Event, Message, Command (wg realnych potrzeb)

Status: plan wdrożenia (akceptacja wymagań)
Data: 2026-08-22
Zakres: SHELL platforma + wszystkie Bounded Context (BC) — definition, execution, ingestion, project, scheduling, session, user.

> **Nota**: dokument zastępuje wcześniejszą wersję „unifikacja outbox do jednej tabeli `outbox`/`inbox`". Po analizie ten wariant jest **odrzucony** — konsolidacja tabel rozwiązuje estetykę schematu, nie realne problemy. Prawdziwy problem leży w tym, że maszyneria dostarczania jest zaprojektowana pod **eventy** (broadcast), a próbuje się przez nią pchać **message** (adresowaną treść) i **command** (intencję). Ten plan porządkuje kanały wg ich natury.

---

## 1. Cel

Uporządkować trzy kanały komunikacji między BC tak, aby każdy był dopasowany do swojej natury:

| Kanał | Natura | Docelowy mechanizm |
|---|---|---|
| **Event** | broadcast faktów, konsekwencja mutacji agregatu | transactional outbox (zostaje) + tanie utwardzenie |
| **Message** | **adresowana treść** (bufor danych, np. tekst) do konkretnego agregatu | content-delivery: kontrakt recipient + bufor, transport point-to-point |
| **Command** | intencja wykonania operacji | bezpośredni kanał (Command Port / HTTP); nie przez async broadcast |

Cele szczegółowe:

1. **Message jako pierwszorzędny kanał systemu agentowego** — przenosi treść (bufor tekstu/kontekst dla agenta), a nie fakt; ma jasną definicję, źródła (API, process, agregat) i adresata.
2. **Zero martwego i zero błędnie użytego kodu** — każda zmiana wynika z inventory (krok 0), nie z estetyki schematu; maszyneria nieużywana i niepotrzebna jest usuwana, nie scalana.
3. **Atomiczność tam, gdzie ma sens** — tylko dla skutków mutacji agregatu (event / message z agregatu); message z API/process mogą być zapisywane niezależnie.
4. **Pełna identyfikowalność** (correlation/causation), ślad audytowy i metryki per kanał.
5. **Kompatybilność wire** — `EnvelopeCodec` bez zmian (kontrakt v1).

Semantyczna separacja Command/Event/Message pozostaje zgodna z `skills/architectural-discipline/{command,event,message}-semantics` (zaktualizowanymi pod kątem message = adresowana treść).

---

## 2. Problemy (obecny stan i to, co rozwiązujemy)

### 2.1. Stan obecny

Trzy pary tabel per BC:

```text
outbox_event   / inbox_event      (eventy)
outbox_message / inbox_message    (message)
outbox_command / inbox_command    (command)
```

Osobne maszyny: 3 procesory inbox (`EventInboxProcessor`, `MessageInboxProcessor`, `CommandInboxProcessor`), 2 publisherowie (`SqlMessageOutboxPublisher`, `SqlCommandOutboxPublisher`), 1 relay (topic `shell.delivery`, routing key `{kind}.{contract_type}` — model **broadcast**).

### 2.2. Defekty, które naprawiamy

| # | Problem | Dowód w kodzie | Konsekwencja |
|---|---|---|---|
| P1 | **Message bez jasnej definicji operacyjnej** — „pasywne dane" bez adresata i natury | `message-semantics` (stara wersja) + `outbox_message` nieużywane | Maszyneria message stoi; brak pierwszorzędnego kanału treści, którego potrzebuje system agentowy |
| P2 | **UoW nie zbiera message z agregatu** — `save()` robi tylko `pull_events()`, nie `pull_messages()`; `stage_messages` martwe | `sql_alchemy_uow_base.py:116` vs `:110` | Message wyemitowane przez agregat są gubione; protokół zapowiada funkcję, która nie działa |
| P3 | **Command wpychane w async broker** jako broadcast (`outbox_command`) | `outbox_command`, `CommandInboxProcessor` — nieużywane w produkcji | Intencje (zwykle synchroniczne) nie powinny iść przez async event-backbone; brak decyzji o kanale |
| P4 | **Maszyneria message/command nieużywana w produkcji** (tylko testy) | `SqlMessageOutboxPublisher`/`SqlCommandOutboxPublisher` tylko w `tests/` | Utrzymanie martwych ścieżek; P4 wymaga decyzji: ożywić (message) albo usunąć (command) |
| P5 | **Brak obsługi dużych buforów** — brak `content_ref`; payload leci przez brokera | kontrakt message = sam `payload` | Broker nie zniesie wielkich treści; konieczna referencja do bufora |
| P6 | **Brak adresowania odbiorcy** — nie ma `recipient_aggregate_id/name` | `DeliveryEnvelope` bez destination | Nie da się routować point-to-point; message nie odróżniają się od eventu |
| P7 | **Routing nieegzekwowany** — konsumenci wiążą goły `#` | `rabbit_inbox_consumer.py:65` (`routing_keys or ["#"]`) | „Łap wszystko" zamiast świadomego wyboru |
| P8 | **Ciche zgubienie publikacji** | `rabbit_delivery_transport.py:58` (`mandatory=False`) | Nieroutowalna wiadomość znika bez śladu |
| P9 | **Audyt tylko eventów** | `sql_alchemy_uow_base.py:187` | Brak śladu dla message/command |
| P10 | **Brak polityk i metryk per kanał** | globalne `max_retries`/backoff w `InboxProcessorBase` | Brak możliwości różnicowania i obserwacji |

> **NIE jest defektem**: osobna sesja publishera dla message z API/process. To celowe — taka message nie jest skutkiem mutacji agregatu, więc nie potrzebuje atomowości z UoW (dual-write nie występuje, bo nie ma stanu do atomizacji).

### 2.3. Co NIE jest problemem

- Separacja kontraktów Command/Event/Message — zostaje (jest poprawna).
- Trzy osobne pary tabel — zostają; konsolidacja została odrzucona.
- Istniejący transactional outbox dla eventów — działający i poprawny.

---

## 3. Metody

| Metoda | Kanał | Opis |
|---|---|---|
| **Transactional Outbox** | Event | deliverable zapisywane atomowo ze stanem; `published_at` po potwierdzeniu transportu; at-least-once |
| **Inbox + lease/claim/retry/DLQ** | Event, Message | wspólny cykl (już w `InboxProcessorBase`); polityki i metryki per kanał |
| **Content Delivery** | Message | adresowany nośnik treści: kontrakt `text`/`content_ref` + `recipient`; duże bufory przez referencję, nie przez payload brokera |
| **Źródło-świadoma atomowość** | Message | API/process → zapis niezależny (własna sesja, brak stanu do atomizacji); agregat → `append_message`→`pull_messages`→`stage_messages` atomowo w UoW |
| **Transport point-to-point** | Message | kolejka per odbiorca lub destination w routingu — nie broadcast zdarzeń |
| **Bezpośredni kanał** | Command | Command Port / HTTP (za `provider-service-separation`); async tylko dla długich, odpornych operacji |
| **Idempotencja** | Event, Message | `ON CONFLICT DO NOTHING` (outbox_id) + `processed_delivery(consumer_name, outbox_id)` |
| **Twarde ograniczenia** | wszystkie | typy/kontrakty zamiast gołych stringów tam, gdzie nowy kod; bez zbędnych CHECK na starych tabelach |
| **Monitoring** | Event, Message | metryki per kanał (claimed/processed/retried/dead_lettered/lag) + alert DLQ |

---

## 4. Uzasadnienie (dlaczego tak, a nie inaczej)

1. **Istniejąca maszyneria jest broadcastowa, a to pasuje tylko do eventu.** Topic `shell.delivery` + routing `{kind}.{contract_type}` to model „publikuj, zainteresowani słuchają". Fakt (event) wpisuje się w to idealnie. Adresowana treść (message) wymaga point-to-point; intencja (command) wymaga bezpośredniego wywołania. Pchanie wszystkich trzech przez jedną maszynerię wymusza nadmiarową złożoność na message/command.
2. **Message to najważniejszy kanał w systemie agentowym.** Treść (tekst/kontekst) przesyłana między agentami jest "mięsem" tego systemu, nie efektem ubocznym. Zasługuje na własny, dopracowany content-delivery, a nie na kopię ścieżki eventów.
3. **Atomiczność jest potrzebna tylko dla skutków mutacji agregatu.** Event zawsze powstaje przy zmianie stanu → atomiczny outbox. Message z agregatu → tak samo (przez `stage_messages` w UoW). Message z API/process nie mają stanu do atomizacji → niezależny zapis do `outbox_message` jest poprawny i prostszy (dual-write nie występuje, bo nie ma transakcji domeny).
4. **Duże bufory wymuszają referencję.** Broker nie jest magazynem treści. Kontrakt message nosi `content_ref` (a dla małych treści `text` inline); koperta transportowa pozostaje lekka.
5. **Konsolidacja tabel została odrzucona.** Dawała mniej tabel, ale nie naprawiała żadnego z P1–P10 i niosła koszt (migracja 6→2, churn ~60 plików, okno przejściowe). Zachowujemy trzy pary tabel i porządkujemy kanały.
6. **Command nie powinien iść przez async broadcast.** Intencja oczekuje wykonania; synchroniczny Command Port (HTTP) daje prostsze obsługiwanie błędów, odpowiedzi i niższą latencję. Async ma sens tylko dla operacji długich/odpornych — wtedy świadoma, mała kolejka, nie event-backbone.

---

## 5. Docelowe definicje i model (odniesienie dla planu)

### 5.1. Semantyka (patrz skille)

- **Event** — „stało się": fakt, broadcast, atomowy ze stanem, bez adresata.
- **Message** — „masz to, weź zapisz": adresowana treść (bufor danych) do wskazanego agregatu; intencja nieistotna; głównym celem jest przekazanie treści; domyślnie prosty zapis, pipeline wieloetapowy jest opcją.
- **Command** — „zrób to, zrób tamto": lekka intencja, może nie mieć danych; kanał bezpośredni.

### 5.2. Tabele — zostają osobne

```text
outbox_event   / inbox_event      (event, broadcast, atomiczny)
outbox_message / inbox_message    (message, content-delivery)
outbox_command / inbox_command    (decyzja w kroku 4: użycie lub usunięcie)
```

### 5.3. Kontrakt Message (docelowy)

`IntegrationMessage` rozszerzony o role treści i adresata:

```python
@dataclass(frozen=True)
class IntegrationMessage:
    message_id: str
    correlation_id: str
    causation_id: str
    occurred_at: datetime
    aggregate_id: str
    aggregate_name: str
    schema_version: int
    # docelowe (regula docelowa — patrz skille):
    text: str | None          # mala tresc inline
    content_ref: str | None   # referencja do duzego bufora
    recipient_aggregate_id: str
    recipient_aggregate_name: str
    stage: int                # pozycja w opcjonalnym pipeline
```

Zasada: `text` XOR `content_ref` (jeden z nich zawsze obecny; nigdy pusty — za `no-empty-fallbacks`). `recipient_*` wskazuje zawsze konkretny agregat.

### 5.4. Wpływ na skille

- `command-semantics` — rozszerzony o kanał (kroki 4/7).
- `message-semantics` — rozszerzony o transport point-to-point i źródło-świadomą atomowość.
- `event-driven-integration` — uzyskał jawną granicę Event/Message/Command.

---

## 6. Plan zmian — punkt po punkcie (z weryfikacją każdego kroku)

Każdy krok ma: **Zmianę** (co → na co), **Jak** (jak zrealizować), **Weryfikację** (jak potwierdzić poprawność).

### Krok 0 — Inventory użycia kanałów (dane, nie intuicja)

- **Zmiana**: brak → raport użycia Event/Message/Command w produkcji.
- **Jak**: przeplatać repozytorium: które BC publikują/odbierają message i komendy poza `tests/`; czy `outbox_message`/`outbox_command` mają choć jednego producenta/konsumenta; liczba kolumn/wierszy w realnych bazach; istniejące handlery `MessageBus`/`CommandBus`.
- **Weryfikacja**: raport udostępniony; decyzje w krokach 3–5 (message: ożywić; command: kanał direct lub usunięcie) oparte na nim, nie na założeniach.

### Krok 1 — Utwardzenie ścieżki eventów (tanie, bez ryzyka)

- **Zmiana**: `rabbit_delivery_transport.py:58` `mandatory=False` → `mandatory=True`; konsumenci wiążą **jawne** wzorce `event.#` zamiast gołego `#`; audyt rozszerzony na wszystkie dostawy event.
- **Jak**: zmienić argument `exchange.publish(..., mandatory=True)`; w konfiguracji kolejki podać wzorce routingu; w `_write_staged_outbox` dopisać audyt dla wszystkich emisji event.
- **Weryfikacja**: test — nieproutowalny event zgłasza błąd (retry/DLQ); `rg 'routing_keys or \["#"\]'` → 0; audyt zawiera recordy wszystkich eventów.

### Krok 2 — Message: kontrakt + źródło-świadoma atomowość

- **Zmiana**: (a) kontrakt `IntegrationMessage` + pola `recipient_aggregate_id/name`, `text`/`content_ref`, `stage` (reguła docelowa); (b) `UoW.save()` zbiera `pull_messages()` obok `pull_events()` i `_write_staged_outbox()` zapisuje `_staged_messages` **atomowo** do `outbox_message`; (c) źródła API/process używają niezależnego publishera (wzorzec `SqlMessageOutboxPublisher` — **zostaje**, osobna sesja jest tu poprawna).
- **Jak**:
  - `save()`: `self.stage_messages(aggregate.pull_messages())`;
  - `_write_staged_outbox()`: wiersze `outbox_message` dla `_staged_messages` (payload przez `DomainMessageSerializer`, `occurred_at`, correlation/causation) w tej samej transakcji;
  - kontrakt wg sekcji 5.3; `text` XOR `content_ref`, `recipient_*` wymagane.
- **Weryfikacja**: test transakcyjny — commit daje wiersz `outbox_message`, rollback **zero** (dla źródła-agregat); test API — message zapisana niezależnie, bez transakcji domeny; test kontraktu — `text`/`content_ref` rozłączne.

### Krok 3 — Message: transport point-to-point

- **Zmiana**: message nie idą broadcastem jak eventy; transport przez kolejki/krotki kluczujące per odbiorca (`recipient`).
- **Jak**: dla message stosować destination-aware routing (kolejka per `recipient_aggregate_name` lub routing key `message.<recipient>.<aggregate_id>`) — binding bez gołego `#`; `RabbitInboxConsumer` dla message wiąże wzorce adresowane.
- **Weryfikacja**: test — message trafia wyłącznie do wskazanego odbiorcy, brak fan-outu; `EnvelopeCodec` bez zmian (kontrakt v1).

<!-- PLAN_PART2 -->

### Krok 4 — Command: decyzja o kanale

- **Zmiana**: `outbox_command`/`CommandInboxProcessor`/`SqlCommandOutboxPublisher` — wg inventory: (a) **usunąć**, jeśli komendy między BC nie istnieją lub przechodzą na Command Port (HTTP); albo (b) zawęzić do świadomych przypadków (długie, odporne operacje) z osobną, małą kolejką.
- **Jak**: jeśli wybór (a) — usunąć tabele `outbox_command`/`inbox_command` z baseline'ów (7 BC), usunąć publisher/procesor, a komendy między BC przenieść na `Command Port` (HTTP, za `aggregate-command-port`/`provider-service-separation`); jeśli (b) — zostawić z jawnym routingiem i politykami.
- **Weryfikacja**: `rg "SqlCommandOutboxPublisher|CommandInboxProcessor"` poza `tests/` → 0 (wybór a) albo tylko uzasadnione użycia; e2e komendy przechodzi nowym kanałem.

### Krok 5 — Sprzątanie maszynerii bez użytkownika (wg inventory)

- **Zmiana**: usunięcie nieużywanych tabel/procesorów/publisherów potwierdzonych w kroku 0 (np. `outbox_command`, puste aliasy `COMMAND_DELIVERY_MODELS`); **bez migracji danych**, gdy tabele są puste.
- **Jak**: usunąć z `baseline.py` listy i `PersistenceDeliveryModels` nieużywane bundle; usunąć testy wyłącznie pod martwe ścieżki (zastąpić testami kroków 2–3).
- **Weryfikacja**: `rg "COMMAND_DELIVERY_MODELS|MESSAGE_DELIVERY_MODELS|EVENT_DELIVERY_MODELS"` — zgodnie z decyzjami; `pytest` przechodzi; `run_tests.ps1` bez błędów.

### Krok 6 — Testy i reguły architektury

- **Zmiana**: testy pod realne kanały + zakazy:
  - `message`: test atomiczności źródła-agregat (rollback=0), test źródła API/process (zapis niezależny), test point-to-point (tylko adresat), test kontraktu (`text` XOR `content_ref`, `recipient` wymagany);
  - `event`: test `mandatory`/błędnego routingu, audyt eventów;
  - **zakaz**: `EventBus`/broadcastowy routing dla message; `CommandBus` w async-outbox (jeśli wybór a); goły `#` w bindingach konsumentów.
- **Jak**: zaktualizować `tests/architecture` i `tests/platform/...`, dodać brakujące testy z kroków 1–4.
- **Weryfikacja**: cały zestaw testów przechodzi; testy architektury blokują niepoprawne użycie kanałów.

### Krok 7 — Dokumentacja i skille

- **Zmiana**: `docs/inbox-outbox-architecture.md`, `shell/platform/doc/{delivery-overview,relay,unit-of-work,transactional-outbox,inbox-processor,delivery-transport,tracing-context}.md`, `shell/README.md`; skille `command-semantics`/`message-semantics`/`event-driven-integration` — opis kanałów wg sekcji 3–5.
- **Jak**: wpisać decyzje z kroków 1–5; message jako content-delivery (recipient, content_ref, dwa źródła), command jako kanał bezpośredni.
- **Weryfikacja**: `rg "pasywne dane|oto dane|widmo konsolidacji"` w docs+skille → 0.

### Krok 8 — Monitoring i alerty per kanał

- **Zmiana**: metryki per kanał (claimed/processed/retried/dead_lettered/lag) z etykietą (event|message) + alert DLQ.
- **Jak**: dodać etykietę do metryk `InboxProcessorBase`; alert gdy `dead_lettered` rośnie w oknie.
- **Weryfikacja**: test metryk — etykieta obecna; dashboard/alert zdefiniowany.

---

## 7. Kryteria zakończenia (definition of done)

1. Inventory (krok 0) wykonany i udokumentowany w tym pliku.
2. Event: `mandatory=True`, jawne bindingi, pełny audyt — bez zmiany kontraktu wire.
3. Message: kontrakt z `recipient`/`text`/`content_ref`; agregat → atomiczny zapis; API/process → niezależny zapis; transport point-to-point.
4. Command: decyzja kanału (direct lub usunięcie) wdrożona; brak nieużywanej maszynerii.
5. Brak tabel `outbox_command`/`inbox_command` w runtime, jeśli wybór (a).
6. `EnvelopeCodec` i wire v1 bez zmian.
7. Testy architektury blokują złe użycie kanałów (message przez broadcast, command przez async outbox, goły `#`).
8. Metryki i alerty per kanał włączone.
9. `run_tests.ps1` przechodzi bez błędów.

---

## 8. Ryzyka i sposób ich zamknięcia

| Ryzyko | Mitigacja |
|---|---|
| Zmiana UoW dotyka wszystkich agregatów | Krok 2 etapami BC po BC; każdy BC w osobnym PR z pełnym testem |
| Ożywienie `stage_messages` łamie obecne zachowanie | Test rollback=0 dla źródeł-agregat; nie zmienia ścieżki eventów |
| Command usuwane, a jednak potrzebne | Krok 0 (inventory) + Krok 4 wybór (b) kolumna awaryjna |
| Duże bufory w brokerze | `content_ref` od kroku 2; test, że payload message pozostaje lekki |
| Brak point-to-point (message jak broadcast) | Krok 3: koleje/kluczowanie per `recipient`; test „tylko adresat" |
| Regresja wire | Zamrożony `EnvelopeCodec` + `test_integration_event_transport_contract.py` w CI |