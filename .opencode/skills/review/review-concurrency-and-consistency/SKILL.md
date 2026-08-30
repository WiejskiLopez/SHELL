---
name: review-concurrency-and-consistency
description: Weryfikacja współbieżności i spójności — transakcje, optymistyczne blokowanie, wyścigi, atomiczność, eventual consistency, kolejność zdarzeń, poprawność współdzielonych stanów. Używaj przy code review pod kątem ryzyk przy równoległym dostępie.
---

# Review — Współbieżność i spójność

> Pierwsza wydana transakcja równoległa, która nadpisze cudzy stan, to realny incydent.

## 1. Granice transakcji

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Transakcja obejmuje dokładnie jedno zadanie (agregat), nie jest zbyt długa | commit po długim IO/API w transakcji | HIGH |
| UoW atomowo zapisuje zmianę + outbox | częściowy zapis → event bez stanu (albo odwrotnie) | **CRITICAL** |
| Zero akcji sieciowych wewnątrz transakcji | HTTP call między `BEGIN` a `COMMIT` | HIGH |
| Brak trzymania transakcji na lockach długo | długoterminowe `SELECT ... FOR UPDATE` | MEDIUM |

## 2. Optymistyczne blokowanie

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Agregat ma wersję (version/rowversion), konflikt zgłaszany błędem | brak zapobiegania nadpisaniu; cichy last-write-wins | **CRITICAL** |
| Konflikt wersji mapowany na odpowiedź 409 dla klientów | nadpisanie bez informacji | HIGH |
| Update warunkowy na wersji w SQL (nie load-modify-save ślepo) | nieetykietowane `UPDATE` bez WHERE na version | HIGH |

Patrz `aggregate-design`.

## 3. Wyścigi i atomiczność

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Check-then-act w operacji bazodanowej atomiczny (WHERE/conditional) | `if exists → insert` bez ochrony (race) | **CRITICAL** |
| Unikalność wymuszona w bazie (constraint/index), nie tylko w kodzie | deduplikacja tylko w warstwie aplikacji | **CRITICAL** |
| Liczniki/sumy/salda aktualizowane atomowo (SQL ustawienie) | read-modify-write licznika | HIGH |
| Blokady (lock) najkrótsze możliwe, jedna na raz | kilka locków naraz → deadlock/eskalacja | MEDIUM |

## 4. Eventual consistency

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Eventual consistency świadoma i udokumentowana dla read model | sync read czeka na async write | MEDIUM |
| Brak zależności od chwilowej spójności w krytycznych walidacjach | walidacja oparta o nieaktualny read | HIGH |
| Kolejność zdarzeń podmiotu deterministyczna (partition key / sequence) | nieokreślona kolejność update'ów tego samego podmiotu | HIGH |

Patrz `event-driven-integration`.

## 5. Współdzielone stany w runtime

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Singletony bez mutacji, albo z synchronizacją | singleton-cache mutowany bez lock | **CRITICAL** |
| Współdzielone zbiory/pliki z bezpiecznym dostępem | dict/listy w singletonie bez locka na zapis | HIGH |
| Stan requestu nie migruje między wątkami/taskami | globalny stan na request (ContextVar bez kontekstu) | HIGH |

Patrz `tracing-context`.

## 6. Checklista finalna

- [ ] Transakcja = 1 zadanie + outbox; zero sieci w transakcji.
- [ ] Optymistyczna wersjonowanie dla modyfikacji.
- [ ] Check-then-act atomiczny; unikalność w bazie.
- [ ] Eventual consistency świadoma.
- [ ] Singletony bez mutacji lub z synchronizacją.