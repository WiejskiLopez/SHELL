# ADR-0002: Grupowanie capability-first obserwowalności w platformie

## Status

Accepted

## Data

2026-08-29

## Kontekst

Platforma jest współdzieloną warstwą techniczną wielu ortogonalnych zdolności
(capabilities): obserwowalność (metryki, readiness), messaging (outbox/inbox),
persistence, autoryzacja, health. Do tej pory całość była uporządkowana
warstwowo (`application/ports`, `infrastructure/`, `framework/`) — efekt jest
taki, że jedna zdolność jest rozproszona po kilku katalogach. Przykładowo
obserwowalność żyła w:

- `shell/platform/application/ports/runtime/metrics.py` i `readiness.py`;
- `shell/platform/infrastructure/metrics/` (registry, backendy);
- `shell/platform/infrastructure/health/` (proby readiness);
- `shell/platform/framework/api/{metrics,health,readiness}.py` i
  `framework/api/middleware/metrics.py`.

Konsekwencje: brak jednego właściciela zdolności, trudna do wyegzekwowania
własność, rozproszona zmiana, duży koszt wejścia w temat. Enterprise practice
dla platformy (współdzielonej, a nie domenowej) stosuje grouping
feature/capability-first z zachowaniem wewnętrznych warstw w każdej zdolności.

## Decyzja

1. Obserwowalność zostaje zgrupowana jako pierwsza zdolność capability-first pod
   `shell/platform/observability/`:

   ```text
   shell/platform/observability/
     application/ports/metrics.py            # MetricsBackend, MetricsExporter, recorders
     application/ports/readiness.py          # ReadinessProbe, ReadinessReport
     infrastructure/metrics/                 # MetricsRegistry, Logging/Prometheus backends
     infrastructure/health/                  # Composite/Rabbit/Sql readiness probes
     framework/api/middleware/metrics.py     # MetricsMiddleware
     framework/api/metrics.py                # /metrics router + instalacja
     framework/api/readiness.py              # /readiness router
     framework/api/health.py                 # mount_readiness
   ```

2. Wewnętrzna struktura zdolności zachowuje warstwy aplikacyjną, infrastrukturalną
   i frameworkową (hexagon), a reguły zależności pomiędzy warstwami obowiązują
   jak dotychczas.
3. Wspólna platforma pozostaje właścicielem granicy: `shell/platform` nie
   importuje ŻADNEGO bounded context (kontrakt import-lintera bez zmian).
4. Migracja polega na przeniesieniu istniejącego kodu (bez duplikacji i bez
   kopii) do docelowych lokalizacji i zaktualizowaniu wszystkich importerów
   (kontenery 7 serwisów, app.py, platforma wewnętrzna, testy, Wiki).
5. Pozostałe zdolności (messaging, persistence, auth, health-level) są
   zgrupowane w osobnych krokach, każdy jako osobny ADR, wyłącznie wtedy, gdy
   mają realny kod — nigdy jako puste katalogi-placeholdery.

## Konsekwencje

- **Pozytywne:** jedna zdolność = jeden katalog i jeden właściciel; spójne
  ścieżki importów (`shell.platform.observability.*`); łatwiejsze egzekwowanie
  własności przez import-linter per-zdolność; zachowany kierunek zależności
  warstw.
- **Negatywne:** zmiana ścieżek importów (przejściowy koszt edycji ~40 plików);
  adresy w Wiki i dokumentach wymagają aktualizacji.
- **Migracja:** wykonana jednorazowo dla obserwowalności; żadnych shimów ani
  aliasów importowych — importery wskazują docelowe ścieżki.