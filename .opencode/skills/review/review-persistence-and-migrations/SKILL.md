---
name: review-persistence-and-migrations
description: Weryfikacja persystencji — repozytoria i symetria kontraktu, zgodność modelu ORM z migracją Alembic, mapper round-trip, outbox/inbox w transakcji, query side. Używaj przy code review warstwy infrastruktury bazodanowej.
---

# Review — Persystencja i migracje

> Każda rozbieżność między modelem a bazą to błąd krytyczny — łamie spójność danych.

## 1. Repozytoria — port i implementacje

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Port repozytorium w `repositories/` domeny, implementacje SQL/InMemory w infrastrukturze | port zdefiniowany w infra; implementacja w domenie | **CRITICAL** |
| Symetria port↔kontrakt — metody portu mają odpowiadające implementacje obu wariantów | SQL ma metodę, której InMemory nie ma | HIGH |
| Metody operują na domenie/ID, nie na ORM | repo przyjmuje/zwraca `Model` | **CRITICAL** |
| Query side (odczyty odczytowe) oddzielone od write | repozytorium wykonuje ciężkie projections razem z zapisami | MEDIUM |
| Repo nie zawiera logiki biznesowej/filtrów decyzyjnych | warunek biznesowy w SQL zamiast specification | HIGH |

Patrz `repository`, `repository-contract-symmetry`, `specification-structure`.

## 2. Model ORM ↔ migracje Alembic

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Każda kolumna w ORM model ma odpowiednik w migracji i odwrotnie | dodano kolumnę bez migracji (albo model bez `nullable`) | **CRITICAL** |
| Migracja idzie w parze ze zmianą kodu (te mesma PR) | model zmieniony, migracja w innym PR | **CRITICAL** |
| Brak niespójności typów (VARCHAR length, default, index) | mismatch type/default/index między modelem a migracją | HIGH |
| Każda zmiana ORM wymaga review zgodności z migracją | zmiana bez retrospektywy model-migration | MEDIUM |

Patrz `model-migration-sync`.

## 3. Mapper i round-trip

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Mapowanie domain↔model symetryczne (round-trip zachowuje stan) | konwersja gubi pole lub zmienia semantykę | **CRITICAL** |
| Test round-trip dla mapperów | brak testu odwracalności | HIGH |
| Mapper nie wykonuje logiki biznesowej | mapper normalizuje/rewaliduje dane domenowe | HIGH |

Patrz `mapper`, `mapper-structure`, `persistence-round-trip`.

## 4. Outbox / Inbox w transakcji

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Zapis eventu do outbox w tej samej transakcji co zmiana stanu | event publikowany przed commita albo w osobnej transakcji | **CRITICAL** |
| Idempotencja przez inbox (deduplikacja po `event_id`) | konsument bez ochrony przed duplikatem | **CRITICAL** |
| Eventy nie gubią się podczas błędów transportu | nie ma retry/DLQ | HIGH |

Patrz `event-driven-integration`.

## 5. Wydajność i poprawność zapytań

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Brak N+1 w ścieżkach read | pętla z zapytania per rekord | HIGH |
| Indeksy pokrywają filtry porządkowania | query filtr na kolumnie bez indeksu przy dużych danych | MEDIUM |
| Lazyloading / eager wybór świadomy | unintencjonalny lazy loading w serializacji | MEDIUM |
| Triggery/funkcje SQL o ograniczonej logice, bez ukrytych side effectów | skomplikowany SQL robiący decyzje domenowe | HIGH |

Patrz `review-performance`.

## 6. Checklista finalna

- [ ] Port-symetria: SQL i InMemory mają identyczny kontrakt.
- [ ] Model ORM i migracja spójne; zmiana/PR razem.
- [ ] Mapper z testem round-trip.
- [ ] Zapis + outbox w jednej transakcji.
- [ ] Brak logiki domenowej w SQL/repo.