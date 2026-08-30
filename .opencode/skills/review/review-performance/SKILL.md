---
name: review-performance
description: Weryfikacja wydajności — N+1, indeksy, blokujące wywołania w async, nieograniczone kolekcje, batchowanie, wybór loading/eager, cache, agregacje po stronie DB. Używaj przy code review gorących ścieżek i zapytań.
---

# Review — Wydajność

> Optymalizuj gorące ścieżki. Za wcześnie zoptymalizowane zimne ścieżki to dług, nie zysk.

## 1. N+1 i zapytania

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Brak N+1 w pętlach (per rekord zapytanie) | foreach z repo call w środku | HIGH |
| Eager loading / joinety tam, gdzie grafy są ładowane razem | lazy loading w serializacji odpowiedzi | HIGH |
| Zapytania/projekcje ograniczone do potrzebnych pól | `SELECT *` z odrzucaniem na poziomie aplikacji | MEDIUM |
| Batchowe operacje dla dużych zbiorów | insert/update per wiersz w pętli (miliony) | HIGH |

## 2. Indeksy i agregacje

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Filtry/porządek w gorących zapytaniach pokryte indeksami | filtr na kolumnie bez indeksu przy dużych danych | MEDIUM |
| Agregacje robione w DB (SUM/COUNT/GROUP BY), nie na wynikach w pamięci | pobranie 100k wierszy do policzenia sumy | HIGH |
| Paginacja (page/keyset), nie `LIMIT offset` na wielkich zbiorach | nieskończona paginacja offsetowa | MEDIUM |
| Brak duplikacji ciężkich zapytań w jednym żądaniu | to samo zapytanie 2x w jednym request | MEDIUM |

Patrz `review-persistence-and-migrations`.

## 3. Async / blokujące wywołania

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Zero blokujących wywołań (requests, sync IO) w event loop | `requests.get` w async handlerze | **CRITICAL** |
| Współbieżność tam, gdzie IO niezależne (asyncio.gather/…), zachowanie limitów | sequential call 5 API | MEDIUM |
| Brak współbieżnego dostępu do pojedynczej współdzielonej zmiany (thundering herd) | 50 równoległych zapytań do cache miss jednocześnie | MEDIUM |

## 4. Pamięć i kolekcje

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Brak nieograniczonych kolekcji w pamięci (bez paginacji/stream) | wczytanie całej tabeli do listy | HIGH |
| Duże pliki/payloady strumieniowane, nie w całości | `response.content` setek MB w RAM | MEDIUM |
| Brak kopii ogromnych struktur bez potrzeby | niepotrzebna materializacja | LOW |

## 5. Cache

| Weryfikacja | Złamanie | Severity |
|-------------|----------|----------|
| Cache z poprawnym TTL i invalidacją spójną ze źródłem | cache bez invalidacji → stale dane biznesowe | HIGH |
| Brak cache'owania danych wrażliwych w sposób niebezpieczny | PII w publicznym shared cache bez ochrony | HIGH |
| Cache nigdy nie jest "źródłem prawdy" dla write | zapis tylko do cache, nie do DB | **CRITICAL** |

## 6. Checklista finalna

- [ ] Zero N+1 i blokujących IO w async.
- [ ] Indeksy pokrywają gorące filtry; agregacje w DB.
- [ ] Duże zbiory paginowane/batchowane.
- [ ] Cache spójny i nigdy nie jest write store.
- [ ] Brak nieograniczonych kolekcji w RAM.