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
shell/application/<bc>/commands/                   # Komendy (DTO)
shell/application/<bc>/command_handlers/           # Handlery komend (1 handler = 1 agregat)
shell/domain/<bc>/aggregates/                      # Agregaty (write model)
shell/domain/<bc>/repositories/                    # Porty repozytoriów
```

### Query side

Query serwisy grupuje się **per agregat**, a nie per BC, co ułatwia ekstrakcję do mikroserwisu:

```
shell/application/<bc>/queries/                    # Query (DTO)
shell/application/<bc>/query_handlers/             # Handlery query
shell/application/<bc>/query_services/
    <nazwa_agregatu>/                              # QueryService dla danego agregatu
        <nazwa>_service.py                         # Grupa powiązanych zapytań
shell/infrastructure/<bc>/projections/             # Projekcje read modelu
```

Przykład:

```
shell/application/execution/query_services/
    workflow/
        workflow_list_service.py
        workflow_detail_service.py
        workflow_summary_service.py
    session/
        session_history_service.py
```

## 10. Podsumowanie — Checklista

Projektując CQRS:
- [ ] Osobne lokacje dla command i query
- [ ] Testy command side z InMemory repos
- [ ] Testy query side z prawdziwą bazą lub mockiem
