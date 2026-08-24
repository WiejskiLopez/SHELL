# Usunięcie kanału Message — decyzja architektoniczna (2026-08-24)

## Decyzja

Kanał **Message** (adresowana treść) zostaje **usunięty** z SHELL. Komunikacja
jest realizowana wyłącznie przez dwa kanały: **Event** (broadcast faktów) i
**Command** (intencja, kanał bezpośredni Command Port / HTTP).

## Powody

1. **Zero użycia w produkcji.** Kanał message nie miał ani producenta
   (`append_message` nie był wywoływany nigdzie poza platformą i testami), ani
   konsumenta (żaden kontener bootstrap nie tworzył `MessageInboxProcessor` ani
   relay `kind="message"`; jedyny referent `SchedulerService` nie był
   instancjonowany). Cała maszyneria opierała się na hipotetycznym potrzebie.
2. **Nadmiarowość semantyczna w tym systemie:**
   - **treść będąca skutkiem faktu** → niesie ją już `IntegrationEvent`
     (przykład: `AuthSessionCreatedIntegrationEvent` → Session BC);
   - **adresowane „masz to, zapisz"** (intencja operacji na agregacie odbiorcy)
     → to domena **Command Port** (`aggregate-command-port`): adresowane,
     z odpowiedzią i jawną obsługą błędów; treść jedzie jako DTO/state_data;
   - event nie nadaje się do adresowanej treści (fałszywy fakt + broadcast
     z filtrowaniem po odbiorcy), dlatego message NIE zostało zastąpione
     eventem — zastąpiło je command.
3. **Utrzymanie martwego kodu** naruszało `outbox.md` §Krok 5 i
   `architectural-discipline`.

## Zakres usunięcia

- kontrakty: `DomainMessage`, `IntegrationMessage`, `MessageId`;
- bus i porty: `MessageBus`, `MessageBusPublisher`, `MessagePublisher`,
  `FakeMessagePublisher`;
- serializacja: `DomainMessageSerializer`, `MessageDeserializer`,
  `MessageEnvelopeSerializer`, `message_registry`;
- maszyneria: `SqlMessageOutboxPublisher`, `MessageInboxProcessor`,
  `InMemoryMessageOutboxStore`, `MessageOutboxRecord`, `stage_messages` w UoW,
  `append_message`/`pull_messages` w `AggregateRoot`;
- persystencja: tabele message outbox/inbox z baseline'ów 7 BC,
  `message_delivery.py`, pole `messages` w `PersistenceDeliveryModels`;
- domeny: `IngestionPayload`, port `ingestion_handler`;
- `SchedulerService` (dormant; jedyny referent maszynerii message);
- testy wyłącznie pod te ścieżki.

## Pathway, gdy treść znów będzie potrzebna

| Przypadek | Kanał |
|---|---|
| treść jako konsekwencja faktu | **Event** (payload IntegrationEvent) |
| proste, adresowane zapisanie/akcja treści | **Command Port** (HTTP) |
| asynchroniczny, wieloetapowy pipeline treści (system agentowy) | **dopiero wtedy** świadomy content-delivery point-to-point (kontrakt z `recipient`/`content_ref`/`stage`) — nie wcześniej |

Zasada: **nie odtwarzaj maszynerii message przed realnym wymaganiem**. Decyzja
o kanale treści (event / command / content-delivery) zawsze wg powyższej tabeli.