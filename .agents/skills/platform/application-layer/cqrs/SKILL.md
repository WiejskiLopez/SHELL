---
name: cqrs
description: Zasady CQRS (Command Query Responsibility Segregation) w architekturze hexagonalnej — separacja read/write modeli, QueryService, read model projections, materialized views, eventual consistency. Używaj gdy projektujesz read side w CQRS, decydujesz o separacji modeli, albo optymalizujesz zapytania.
---

# CQRS w Enterprise DDD

## 1. Podstawowa Zasada

**Command** (zapis) i **Query** (odczyt) mają OSOBNE modele. Żaden handler nie robi jednocześnie read i write.

## 2. Command Side (Write Model)

## 3. Query Side (Read Model)

## 4. Query Handler

## 5. Read Model Projections

## 6. Kiedy Separować Modele

| Sytuacja | Command Model | Query Model |
|----------|---------------|-------------|
| Agregat z bogatą logiką | Tak (agregat) | Osobny read model |
| Prosty CRUD | Opcjonalnie (może być ten sam) | Ten sam model |
| Złożone raporty | N/A | Osobny materialized view |
| Wiele źródeł danych | N/A | Osobna projekcja |
| Performance czytania | Niezoptymalizowany | Zoptymalizowany pod odczyt |

## 7. Eventual Consistency między Read a Write

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
shell/application/<bc>/<aggregate>/commands/           # Komendy (DTO) per agregat
shell/application/<bc>/<aggregate>/command_handlers/   # Handlery komend per agregat
shell/domain/<bc>/aggregates/<aggregat>/               # Agregaty (write model)
shell/domain/<bc>/aggregates/<aggregat>/repositories/  # Porty repozytoriów per agregat
```

### Query side

Query grupuje się **per agregat**, co ułatwia ekstrakcję do mikroserwisu:

```
shell/application/<bc>/<aggregate>/queries/            # Query (DTO) per agregat
shell/application/<bc>/<aggregate>/query_handlers/     # Handlery query per agregat
shell/infrastructure/<bc>/<aggregate>/persistence/sql/ # SQL modele i repozytoria per agregat
```

## 10. Podsumowanie — Checklista

Projektując CQRS:
- [ ] Osobne lokacje dla command i query
- [ ] Testy command side z InMemory repos
- [ ] Testy query side z prawdziwą bazą lub mockiem
