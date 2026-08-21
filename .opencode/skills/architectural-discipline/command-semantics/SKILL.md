---
name: command-semantics
description: "Semantyka Command w architekturze SHELL: jawna intencja wykonania operacji biznesowej. Uzywaj przy projektowaniu, review, handlerach, busach i serializacji komend."
---

# Command Semantics

## Definicja

`Command` jest jawnym poleceniem wykonania operacji. Wyraza intencje nadawcy, np. utworzenie, zmiane, usuniecie albo uruchomienie zachowania.

Command ma semantyke intencji wykonania operacji biznesowej. Event opisuje fakt, ktory juz zaszedl, a Message przenosi pasywne dane.

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
- Identyfikator Command opisuje konkretne zadanie, a `event_id` opisuje fakt powstaly po wykonaniu zadania.
- `schema_version` Command opisuje schemat polecenia i jest niezalezny od schematu eventu oraz Message.
- Retry Command powtarza intencje wykonania, a fakt biznesowy powstaje po udanej zmianie agregatu i emisji DomainEvent.

## Testy

Testuj osobno:

- routing Command do wlasciwego handlera;
- walidacje danych Command;
- wykonanie operacji przez agregat;
- emisje eventu przez agregat;
- osobny kontrakt Command, Message i Event.
