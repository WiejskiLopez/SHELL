---
name: cqrs
description: Zasady CQRS (Command Query Responsibility Segregation) w architekturze hexagonalnej — separacja read/write modeli, QueryService, read model projections, materialized views, eventual consistency. Używaj gdy projektujesz read side w CQRS, decydujesz o separacji modeli, albo optymalizujesz zapytania.
---

# CQRS w Enterprise DDD

## 1. Podstawowa Zasada

**Command** (zapis) i **Query** (odczyt) mają OSOBNE modele. Każdy handler realizuje
jedną z dwóch dróg: zapis (Command) albo odczyt (Query).

## 2. Command Side (Write Model)

Write model opiera się na agregatach domenowych. Przepływ zapisu:

```text
Command (DTO) -> CommandBus -> CommandHandler -> Agregat (metoda domenowa)
    -> UoW zapis + outbox -> DomainEvent -> EventBus
```

- Komenda to zamrożony dataclass reprezentujący intencję; logika i stan domeny żyją w warstwie domenowej.
- CommandHandler koordynuje: pobiera agregat przez port repozytorium, wywołuje metodę domenową, zapisuje przez UoW; decyzje biznesowe podejmuje agregat.
- Jeden handler obsługuje dokładnie jeden agregat (mutacja pojedynczego agregatu na transakcję).
- Zapis jest atomowy: agregat + staged eventy + outbox w jednej transakcji UoW.

## 3. Query Side (Read Model)

Read model jest niezależny od write modelu i zoptymalizowany pod odczyt; bazuje na projekcjach, a agregaty i porty repozytoriów domenowych służą wyłącznie write side.

- Query to zamrożony dataclass opisujący żądanie odczytu.
- Query Handler odczytuje przez **QueryService** (port w `application/<bc>/<aggregate>/ports/<agregat>_query_service.py`); odczyt omija UnitOfWork (read-only, bez transakcji zapisu).
- Wynik to DTO (frozen dataclass z typami prostymi); encje domenowe i ORM modele pozostają po stronie write/persistence.

## 4. Query Handler

- Stateless, read-only: wykonuje wyłącznie odczyt (bez mutacji stanu, bez UoW zapisu, bez wywołań mutujących).
- Publikuje zapytanie przez `QueryBus` (każde zapytanie jest zarejestrowane).
- QueryService dostarczany jest przez handler zapytania; framework przekazuje query serwisy wyłącznie do query handlerów.

## 5. Read Model Projections

Read model jest budowany jako projekcja stanu zapisywanego przez command side — zgodnie z lokalizacją per agregat (sekcja 9).

- Odczyt wykonuje operacje read; projekcje są idempotentne.
- Zmiana schematu write modelu wymaga migracji projektji read modelu.
- Read model budowany jest przez projekcje/zapytania; metody domenowe agregatów służą write side.

## 6. Kiedy Separować Modele

| Sytuacja | Command Model | Query Model |
|----------|---------------|-------------|
| Agregat z bogatą logiką | Tak (agregat) | Osobny read model |
| Prosty CRUD | Opcjonalnie (może być ten sam) | Ten sam model |
| Złożone raporty | N/A | Osobny materialized view |
| Wiele źródeł danych | N/A | Osobna projekcja |
| Performance czytania | Niezoptymalizowany | Zoptymalizowany pod odczyt |

## 7. Eventual Consistency między Read a Write

Read model aktualizowany jest poza transakcją write modelu. Aktualizację zapewniają eventy domenowe:

- Agregat emituje `DomainEvent` przy każdej mutacji (zapis w tej samej transakcji co stan — outbox).
- Read model reaguje na event przez event handler i odświeża swoją projekcję (eventual consistency).
- Akceptuj okno niespójności: read model może być chwilowo opóźniony względem write modelu.
- Gdy odczyt wymaga natychmiastowej spójności, używasz tego samego modelu (brak separacji); synchronizacja w tej samej transakcji pozostaje poza read-side.

## 8. Materialized Views

Dla często czytanych, rzadko zmienianych danych — materialized view.

```sql
-- migration
CREATE MATERIALIZED VIEW execution_summary AS
SELECT 
    e.id,
    e.graph_id,
    g.name AS graph_name,
    e.status,
    e.created_at,
    COUNT(et.id) AS task_count,
    COUNT(et.id) FILTER (WHERE et.status = 'COMPLETED') AS completed_tasks
FROM executions e
JOIN graphs g ON g.id = e.graph_id
LEFT JOIN execution_tasks et ON et.execution_id = e.id
GROUP BY e.id, g.name;

-- Refresh (np. po każdej zmianie execution)
REFRESH MATERIALIZED VIEW execution_summary;
```

## 9. Lokalizacja

### Command side

```
shell/<service>/application/<bc>/<aggregate>/commands/           # Komendy (DTO) per agregat
shell/<service>/application/<bc>/<aggregate>/command_handlers/   # Handlery komend per agregat
shell/<service>/domain/<bc>/aggregates/<aggregat>/               # Agregaty (write model)
shell/<service>/domain/<bc>/aggregates/<aggregat>/repositories/  # Porty repozytoriów per agregat
```

### Query side

Query grupuje się **per agregat**, co ułatwia ekstrakcję do mikroserwisu:

```
shell/<service>/application/<bc>/<aggregate>/queries/            # Query (DTO) per agregat
shell/<service>/application/<bc>/<aggregate>/query_handlers/     # Handlery query per agregat
shell/<service>/application/<bc>/<aggregate>/ports/              # QueryService (port) per agregat
shell/<service>/infrastructure/<bc>/<aggregate>/persistence/sql/ # SQL modele i repozytoria per agregat
```

## 10. Podsumowanie — Checklista

Projektując CQRS:
- [ ] Osobne lokacje dla command i query
- [ ] Testy command side z InMemory repos
- [ ] Testy query side z prawdziwą bazą lub mockiem
