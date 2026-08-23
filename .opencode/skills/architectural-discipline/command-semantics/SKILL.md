---
name: command-semantics
description: "Semantyka Command w architekturze SHELL: jawna intencja wykonania operacji biznesowej. Uzywaj przy projektowaniu, review, handlerach, busach i serializacji komend."
---

# Command Semantics

## Definicja

`Command` jest jawnym poleceniem wykonania operacji. Wyraza intencje nadawcy, np. utworzenie, zmiane, usuniecie albo uruchomienie zachowania.

Command ma semantyke intencji wykonania operacji biznesowej. Command jest **lekka i prosta**; moze nie zawierac zadnych danych: `Command -> "zrob to, zrob tamto"`.

Rozgraniczenie z innymi kontraktami jest czescia wlasnej definicji: Command kaze odbiorcy wykonac operacje, nie przenosi tresci ani faktu. Semantyke Event i Message opisuja `event-semantics` i `message-semantics`.

## Kanal

Command jest intencja i domyslnie wywoluje sie **bezposrednio**, a nie przez async broadcast:
- w ramach BC: Command Bus + Command Handler;
- miedzy BC: Command Port (HTTP) za `aggregate-command-port` / `provider-service-separation` — szybka komenda z odpowiedzia i jawna obsluga bledow.

Command nie wymaga outboxa ani brokera do dzialania. Async delivery (osobna, mala kolejka) stosuj **swiadomie** tylko dla operacji dlugich i odpornych na chwilowa niedostepnosc.

## Przeplyw

```text
Command -> CommandBus -> CommandHandler -> Aggregate -> DomainEvent
```

Command handler wykonuje intencje przez agregat. Dopiero agregat emituje event jako fakt skutecznej zmiany.

## Obowiazki

- Command ma osobny typ, registry, serializer, deserializer i `CommandBus`.
- Command handler jest wlascicielem wykonania przypadku uzycia, a reguly biznesowe pozostaja w agregacie.
- Agregat emituje DomainEvent po udanej zmianie stanu.
- Command korzysta z wlasnego serializera i deserializera.
- Command korzysta z `CommandBus` jako kanalu intencji operacyjnych.

## Tozsamosc i wersjonowanie

- Identyfikator Command opisuje konkretne zadanie/request, jezeli kontrakt go wymaga.
- `schema_version` Command opisuje schemat polecenia.
- Retry Command powtarza intencje wykonania; fakt biznesowy powstaje po udanej zmianie agregatu.

## Testy

Testuj osobno:

- routing Command do wlasciwego handlera;
- walidacje danych Command;
- wykonanie operacji przez agregat;
- emisje eventu przez agregat;
- osobny kontrakt Command, Message i Event.
