---
name: review-error-handling-and-logging
description: Weryfikacja obsługi błędów i logowania — dedykowane wyjątki domenowe, propagacja zamiast połykania, poziomy logowania, structured logging, correlation ids, brak sekretów w logach. Używaj przy code review ścieżek błędów i logowania.
---

# Review — Obsługa błędów i logowanie

> Cichy błąd to błąd, którego nie ma w monitoringu — czyli najgorszy błąd.

## 1. Wyjątki domenowe

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Reguły biznesowe rzucają dedykowane wyjątki domenowe | ogólny `ValueError`/`RuntimeError`/`AssertionError` dla biznesu | HIGH |
| Domain error bazuje na wspólnej bazie i jest mapowany na odpowiedź | surowy wyjątek frameworka wycieka do API | HIGH |
| Wyjątki nie są używane jako przepływ sterowania w normalnej ścieżce | `except` do podejmowania normalnej decyzji | HIGH |
| Brak przechwytywania szerokiego `Exception` bez wyraźnej przyczyny | `except Exception: pass` | **CRITICAL** |

Patrz `domain-invariant`, `guard-clause-pattern`.

## 2. Propagacja i połykanie błędów

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Błędy propagowane do warstwy, która potrafi je obsłużyć | handler połyka `Exception` i zwraca `None` | **CRITICAL** |
| Brak operowania pustymi fallbackami przy błędach | `except: return ""` / przeciętny fallback | **CRITICAL** (patrz no-empty-fallbacks) |
| Błędy integracyjne rejestrowane i odtwarzane (retry/DLQ) | błąd transportu cicho ignorowany | **CRITICAL** |
| `except` precyzyjny do typu wyjątku | broad catch w miejscu, gdzie typ jest znany | MEDIUM |

## 3. Logowanie

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Wydarzenia biznesowe/techniczne logowane na właściwych poziomach (info/warn/error) | wszystko debug; błędy bez `logger.error` | MEDIUM |
| Wyjątki logowane z tracebackiem w miejscu obsługi | `logger.error(str(e))` bez śladu | LOW |
| Brak logowania sekretów (hasła, tokeny, dane osobowe) | token w logu | **BLOCKER** |
| Structured logging z correlation_id | logi bez kontekstu korelacji | MEDIUM |
| Brak nadmiarowego logowania w pętlach/najczęstszych ścieżkach | log per wiersz w milionach wierszy | LOW |

Patrz `tracing-context`, `review-security`.

## 4. Granica API i mapowanie błędów

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Ujednolicone mapowanie wyjątków na kody HTTP (409, 404, 400, 500) | różne formaty błędów z różnych handlerów | MEDIUM |
| Identyfikatory błędów ponowne (error code) do logów | klient nie może zgłosić błędu | LOW |
| Nieprzewidziane błędy logowane jako error z correlation | `500` bez śladu jaki event/podmiot | MEDIUM |

## 5. Checklista finalna

- [ ] Zero `except Exception: pass` / cichego połykania błędów.
- [ ] Reguły biznesowe → dedykowane wyjątki domenowe.
- [ ] Logi z correlation_id, bez sekretów.
- [ ] Błędy integracji trafiają do retry/DLQ.
- [ ] Nieprzewidziane wyjątki zostawiają ślad w monitoringu.