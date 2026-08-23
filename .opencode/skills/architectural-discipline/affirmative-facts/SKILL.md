---
name: affirmative-facts
description: "Zasady zapisywania faktow w skillach: fakty sa twierdzacymi opisami tego, czym cos jest, co robi i jakie ma wlasnosci. Uzywaj przy tworzeniu, aktualizacji i review plikow SKILL.md."
---

# Affirmative Facts

## Cel

Skill jest zbiorem prawdziwych, sprawdzalnych faktow o sposobie pracy, architekturze, kodzie lub procesie.

Fakt daje czytelnikowi wiedze o rzeczywistosci:

- czym jest obiekt;
- jaka jest jego odpowiedzialnosc;
- jakie ma wejscia i wyjscia;
- jakie wlasnosci zachowuje;
- jaki przeplyw realizuje;
- gdzie znajduje sie jego implementacja lub kontrakt.

## Forma faktu

Fakt zapisuj zdaniem twierdzacym z jawnym podmiotem i orzeczeniem.

```text
Message przenosi adresowana tresc.
Command wyraza intencje wykonania operacji.
Event opisuje fakt, ktory juz zaszedl.
UnitOfWork przechowuje DomainEvent.
Mapper tworzy IntegrationEvent na podstawie DomainEvent.
```

Kazde zdanie powinno odpowiadac na pytanie: jaka prawdziwa wiedze otrzymuje czytelnik?

## Zasada pozytywnego opisu

Skill opisuje stan docelowy albo potwierdzony stan aktualny. Regula wynika z pozytywnej definicji wzorca:

```text
Serializer przeksztalca obiekt kontraktu w payload.
Deserializer odtwarza obiekt kontraktu z payloadu.
Registry laczy stabilna nazwe kontraktu z jego klasa.
Outbox zapisuje event atomowo z lokalna zmiana stanu.
```

Opis pozytywny wskazuje wzorzec, odpowiedzialnosc i oczekiwany rezultat. Czytelnik moze na jego podstawie zbudowac poprawne rozwiazanie.

## Przeksztalcenie opisu w fakt

Opis architektoniczny uzyskuje wartosc faktu przez wskazanie semantyki, odpowiedzialnosci i kontraktu.

Regule nadaj forme pozytywna przez wskazanie wlasciwego wzorca:

```text
Semantyka:
Message jest pasywnym obiektem danych.

Odpowiedzialnosc:
Message przenosi dane pomiedzy komponentami.

Kontrakt:
Message ma osobny registry, serializer i deserializer.
```

Kazdy fragment opisujacy granice zawiera pozytywna odpowiedzialnosc obiektu lub wlasciwy kontrakt, do ktorego implementacja nalezy.

## Fakt, reguła i zalecenie

Skill rozroznia trzy rodzaje twierdzen:

- `Fakt` opisuje stan potwierdzony w kodzie, tescie lub kontrakcie.
- `Regula` opisuje wymagany stan architektury lub procesu.
- `Zalecenie` opisuje preferowany kierunek projektowy wraz z uzasadnieniem.

Oznaczaj rodzaj twierdzenia naglowkiem, gdy czytelnik moze pomylic stan obecny z docelowym:

```text
## Fakt aktualny
## Regula docelowa
## Zalecenie projektowe
```

## Dowod faktu

Fakt techniczny lacz z dowodem:

- sciezka pliku;
- nazwa klasy, funkcji lub kontraktu;
- test;
- komenda walidacyjna;
- dokumentacja z okresem obowiazywania.

Przyklad:

```text
Fakt: SqlAlchemyUnitOfWorkBase przechowuje DomainEvent.
Dowod: shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py, _staged_events.
Walidacja: test kontraktu UoW sprawdza typ staged eventow.
```

## Jezyk skilla

- Uzywaj precyzyjnych rzeczownikow: `Message`, `Command`, `Event`, `payload`, `envelope`, `registry`, `mapper`.
- Uzywaj czasownikow opisujacych odpowiedzialnosc: `jest`, `opisuje`, `przechowuje`, `mapuje`, `serializuje`, `deserializuje`, `publikuje`, `kopiuje`, `waliduje`.
- Jedno zdanie opisuje jedna zaleznosc lub jedna odpowiedzialnosc.
- Przyklad pokazuje kompletny poprawny stan oraz jego odpowiedzialnosci.
- Zdanie prowadzi czytelnika do prawdy, ktora da sie sprawdzic w kodzie albo tescie.

## Struktura skilla

Kazdy skill powinien w tej kolejnosci opisac:

1. definicje obiektu lub wzorca;
2. odpowiedzialnosc;
3. wejscia i wyjscia;
4. relacje z innymi obiektami;
5. przeplyw;
6. przyklad poprawnego zastosowania;
7. dowod lub test kontraktu.

## Kryterium review

Skill jest gotowy, gdy kazde jego glowne twierdzenie:

- opisuje konkretny stan, zachowanie albo kontrakt;
- ma jasny podmiot;
- prowadzi do wiedzy o prawdzie domenowej lub technicznej;
- wskazuje wlasciwy wzorzec implementacji;
- pozostaje zgodne z kodem i testami albo jest jawnie oznaczone jako reguła docelowa.
