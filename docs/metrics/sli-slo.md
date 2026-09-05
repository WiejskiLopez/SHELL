# SLI / SLO dla usług SHELL

Status: **propozycja do kalibracji na stagingu**. Metryki bazowe są już
eksportowane przez `/metrics` (Prometheus text format) — patrz
`shell/platform/doc/metrics.md` i metryki w `shell/platform/observability/infrastructure/metrics/`.

## Zasada

SLO definiujemy per usługa jako 30-dniowe okno rolling (error budget 30 dni).
Alert page'ujemy przy wyczerpaniu budżetu, a warning przy prognozie wyczerpania
w ciągu 24h.

## Wspólne SLI

| SLI | Metryka | Propozycja SLO |
|-----|---------|----------------|
| Dostępność API (HTTP 2xx/3xx/4xx bez 5xx) | `rate(http_requests_total{status=~"5.."}) / rate(http_requests_total)` | 99.5% / 30d |
| Latencja p95 API | `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` | ≤ 800 ms |
| Inbox backlog (PENDING+RETRY) | `inbox_backlog_pending + inbox_backlog_retry` | ≤ 10 000 / 30d |
| Wiek najstarszej wiadomości oczekującej | `inbox_oldest_pending_age_seconds` | ≤ 15 min p95 |
| Outbox backlog (niewysłane) | `outbox_backlog_pending` | ≤ 1 000 / 30d |
| Powodzenie dostawy (0 DLQ) | `inbox_backlog_dead_letter` | ≤ 50 / 30d |
| Zależność HTTP (breaker nie otwarty) | `http_outbound_circuit_state` (0=closed) | 0 otwarć > 5 min / 30d |

## Per usługa (wymiar)

- **user, definition, session, execution, scheduling, project, ingestion** —
  wszystkie SLI z tabeli wspólnej.
- Wyjątki:
  - `http_outbound_*` istotne tylko dla **execution** (jedyna usługa z
    outbound HTTP do definition/session).
  - `outbox_backlog_pending` dla usług z outbox-em (wszystkie z brokerem).

## Alerty (gotowe reguły w `alerts.yml`)

- `ShellApiErrorBudgetBurn` — 5xx > SLO w 5m.
- `ShellLatencyP95Breach` — p95 > 800 ms przez 10m.
- `ShellInboxBacklogHigh` — backlog > 10 000 przez 15m.
- `ShellInboxAgeHigh` — wiek najstarszej > 15 min przez 5m.
- `ShellOutboxBacklogHigh` — > 1 000 przez 15m.
- `ShellDeadLetterGrown` — DLQ > 50 przez 15m.
- `ShellCircuitOpen` — `http_outbound_circuit_state == 1` dłużej niż 5 min.

## Error budget

- Budżet = `(1 − SLO) × 30d`. Dla 99.5% to ok. 3.6 godz. przestoju na 30 dni.
- Page: burn > 100% budżetu w oknie; warning: prognoza wyczerpania ≤ 24h.