---
name: message-semantics
description: "STATUS: KANAŁ MESSAGE USUNIĘTY (2026-08-24). Niniejszy skill opisuje historiczną semantykę i warunki, w jakich kanał treści mógłby wrócić. Używaj wyłącznie przy ocenie, czy realna potrzeba uzasadnia ponowne wprowadzenie content-delivery."
---

# Message Semantics

## STATUS: kanał usunięty

Kanał **Message** (adresowana treść) został **usunięty** z SHELL 2026-08-24 —
nie miał ani producenta, ani konsumenta w produkcji; komunikację realizują
wyłącznie **Event** (broadcast faktu) i **Command** (intencja, Command Port/HTTP).
Decyzja i uzasadnienie: `docs/messages-removed.md`.

**Nie odtwarzaj maszynerii message bez realnego wymagania.** Poniższa semantyka
opisuje tylko *jak wyglądałby* kanał treści, gdyby taka potrzeba faktycznie
istniała (np. asynchroniczny, wieloetapowy pipeline treści systemu agentowego).
Decyzja o kanale treści zawsze wg tabeli w `docs/messages-removed.md`:
skutek faktu → **event**; proste adresowane zapisanie/akcja → **Command Port**;
dopiero długofalowy pipeline → **content-delivery** wg poniższych reguł.

## Definicja

`Message` jest adresowanym nosnikiem tresci. Przenosi dane — przede wszystkim **bufor danych** (tekst lub inna tresc) — od zrodla do wskazanego odbiorcy.

W Message najwazniejsza jest **tresc** (bufor danych). Intencja nie jest istotna: Message nie wyraza operacji, tylko przekazuje tresc.

## Rozdzielenie od innych kontraktow

Message ma **osobna semantyke, kontrakt i kanal** od Command i Event. Rozgraniczenie jest czescia definicji wlasnej tresci:

```text
Message -> "masz to, wez zapisz"   (adresowana tresc; dane dla odbiorcy)
```

Message przenosi tresc do **wskazanego odbiorcy**. Detale semantyki Command i Event znajduja sie w `command-semantics` i `event-semantics` — ten skill ich nie opisuje.

## Zrodla Message

Message moze powstac w trzech warstwach:

- w warstwie **API** — tresc trafia z frontu/klienta do bufora;
- w warstwie **process** — proces generuje tresc dla kolejnego skladnika;
- w **agregacie** — agregat wysyla tresc przez `append_message` po zmianie stanu.

Zrodla API i process tworza Message w warstwie aplikacyjnej i nie wymagaja atomowosci z wlasna zmiana stanu domeny. Agregat tworzy Message: `append_message` buforuje w `_messages`, warstwa aplikacji odbiera przez `pull_messages`.

## Odbiorca

Message jest zawsze adresowana do konkretnego agregatu. Kontrakt Message okresla adresata:

- `recipient_aggregate_id` — docelowy agregat;
- `recipient_aggregate_name` — typ docelowego agregatu.

Message **nie wyraza operacji**: przekazuje tresc, a decyzja, co z nia zrobic, nalezy do agregatu odbiorcy albo Command Handlers.

## Tresc i duze bufory

Message moze przenosic duze bufory danych. Duza tresc nie jest umieszczana w kopercie transportowej w calosci:

- mala tresc: pole `text` (inline);
- duza tresc: pole referencji (`content_ref`) do przechowywanego bufora; odbiorca pobiera tresc na zadanie.

Koperta transportowa pozostaje lekka; broker nie przenosi wielkich dokumentow w payload. Zasada `text` XOR `content_ref` — jeden z nich jest zawsze obecny, nigdy pusty.

## Transport — point-to-point

Message jest adresowana do konkretnego agregatu, wiec transport jest **point-to-point**, nie broadcast jak Event. Routing kieruje wylacznie do `recipient` (kolejka per odbiorca albo klucz routingu destination); brak fan-outu. Kolejka konsumenta nie wiaze wzorca „lap wszystko" (`#`) dla message.

## Zrodlo-swiadoma atomowosc

Zmiana-stanu nie jest zrodlem message zawsze. Sposob zapisu do outboxa message zalezy od zrodla:

- **API / process** — message nie jest skutkiem mutacji agregatu; niezalezny zapis do outboxa message (wlasna sesja publishera) jest poprawny — nie ma stanu domeny do atomizacji;
- **agregat** — message powstaje przy zmianie stanu (`append_message`); zapis atomowy przez UoW (`pull_messages` → `stage_messages` → outbox message w tej samej transakcji).

Message z agregatu nigdy nie jest gubiona miedzy commitem domeny a outboxem; zapis i stan domeny tworza jedna transakcje.

## Przeplyw Message

```text
zrodlo (API | process | agregat)
    -> Message (DomainMessage / IntegrationMessage)
    -> outbox message
    -> relay -> transport
    -> inbox message
    -> MessageInboxProcessor -> MessageBus -> handler
    -> agregat odbiorcy
```

## Dwa przeplywy

Message najczesciej jest **prostym zapisem tresci do wskazanego agregatu** — pojedyncza dostawa, odbiorca zapisuje bufor danych albo wykorzystuje go jako kontekst.

Wieloetapowy pipeline jest **opcjonalnym wariantem**, stosowanym wtedy, gdy tresc musi przejsc transformacje przez kolejne agregaty. Nie jest regula — domyslnym przeplywem jest prosty zapis do odbiorcy.

## Przeplyw wieloetapowy (opcjonalny)

Message moze wywolac ciag automatycznego przetwarzania tresci:

```text
fron -> agregat A (zapis bufora) -> agregat B (transformacja) -> agregat C (dalsza transformacja)
```

Pipeline Message jest **wielotransakcyjny i wieloetapowy**: kazda noga to osobna transakcja i osobna dostawa. Wymagania:

- **trwaly stan procesu** — pozycja Message w pipeline jest utrwalana, awaria nie gubi przebiegu;
- **idempotencja per etapt** — kazdy odbiorca deduplikuje dostawy po `outbox_id`;
- **determinizm transformacji** — retry transformacji daje identyczny wynik albo jest no-op, wiec lancuch nie tworzy duplikatow;
- **kolejnosc** — sasiednie etapy nie wyprzedzaja sie; `causation_id` wiaze etapt z poprzednim.

`message_id` identyfikuje lancuch tresci; `causation_id` wskazuje poprzedni etapt; kazda noga ma wlasny `outbox_id`.

## Wlasnosc i kanaly

- `DomainMessage` i `IntegrationMessage` maja osobny kontrakt, registry, serializer, deserializer, bus, outbox i inbox.
- `message_id` identyfikuje tresc Message.
- Referencja do powiazanego faktu w kontrakcie Message (jesli wystepuje) opisuje zaleznosc tresci od faktu — szczegoly faktu opisuje `event-semantics`.
- `schema_version` Message dotyczy schematu tresci Message.

## Pola czasu

Pole czasu w Message opisuje techniczny czas utworzenia, wyslania lub odebrania tresci (`created_at`, `sent_at`, `received_at`). Nowe kontrakty stosuja nazwe zgodna z semantyka, np. `created_at`, `sent_at` lub `received_at`.

## Implementacja

- Message przenosi tresc pomiedzy komponentami.
- Handler Message zapisuje tresc albo przekazuje ja dalej.
- Decyzja biznesowa nalezy do agregatu odbiorcy albo osobnego komponentu domenowego.
- `MessageSerializer` i `MessageDeserializer` maja osobny kontrakt od serializerow eventow (patrz `event-semantics`).

## Istniejacy kod i stan docelowy

Kanał Message oraz klasy `DomainMessage`, `IntegrationMessage`, `MessageBus` (oraz `append_message`/`pull_messages`/`stage_messages`) **zostały usunięte** z SHELL 2026-08-24 — obecnie nie istnieją w kodzie. Decyzja i pełna lista usuniętych artefaktów: `docs/messages-removed.md`.

**Nie odtwarzaj tych artefaktów jako istniejących.** Poniższe zapisy opisują wyłącznie **kształt kontraktu docelowego, gdyby kanał treści został ponownie wprowadzony**. Do tego czasu obowiązuje semantyka z sekcji STATUS: fakt → **event**, prosta adresowana akcja → **Command Port**, a kanał treści pozostaje niedostępny.

Reguła docelowa (tylko jako projekt, nie jako bieżący stan): kontrakt Message uzupełnia się o adresata (`recipient_aggregate_id`, `recipient_aggregate_name`), pole tresci (`text` i/lub `content_ref`) oraz pole etapu pipeline (`stage`). Mapping Message nie tworzy faktu, tylko przekazuje tresc.