# ADR-0003: Własny MetricsRegistry zamiast standardowego klienta (Prometheus/OTel)

## Status

Accepted

## Data

2026-08-29

## Kontekst

Endpoint `/metrics` platformy renderuje metryki przez własną, minimalną
implementację formatu Prometheus (`MetricsRegistry` w
`shell/platform/observability/infrastructure/metrics/registry.py`), która
ręcznie emituje `text/plain; version=0.0.4` (counter, gauge, histogram),
jest wolna od zewnętrznych zależności i pokryta testami jednostkowymi.

Alternatywą jest adopcja standardowego klienta (prometheus-client lub
OpenTelemetry SDK). Decyzja ta jest strategiczna dla platformy i dotyczy
zewnętrznej granicy (interop z ekosystemem Prometheus/Grafana), dlatego
wymaga formalnego ADR — jest to element Etapu 0 planu z `1.md`.

## Decyzja

Utrzymujemy własny `MetricsRegistry` jako źródło prawdy dla `/metrics`,
przyjmując:

1. **Zakres** — stały, mały zbiór metryk platformowych o niskiej kardynalności
   (HTTP, delivery/inbox/outbox, retry, circuit breaker) z etykietami
   `service`, `method` i ograniczonymi wymiarami stanu.
2. **Zabezpieczenie zgodności** — test kontraktowy w CI parsujący wyjście
   rejestru przez parser referencyjny Prometheus (`promtool check metrics` lub
   oficjalny parser), weryfikujący poprawność formatu, escaping HELP i etykiet,
   kluczy histogramów i semantyki `_total`.
3. **Kontrakt `observability.v1`** — nazwy metryk, typy, jednostki, HELP
   i obowiązkowe etykiety zostają ujednolicone i przypięte testem, aby nie
   rozjechać semantyki.
4. **Port jako granica wymiany** — rejestr pozostaje za portami
   `MetricsExporter`/`MetricsRegistry`; wymiana na prometheus-client/OTel
   w przyszłości jest zmianą wewnętrzną zdolności, bez zmian w kontenerach
   serwisów i importerach.

## Konsekwencje

### Pozytywne

- zero nowych zależności w platformie (powierzchnia dostaw i audytu
  bezpieczeństwa bez zmian);
- pełna kontrola nad wyjściem, kardynalnością i zachowaniem przy awarii;
- swap na standardowy klient pozostaje niski kosztowo (za portem);
- test zgodności z parserem referencyjnym domyka główne ryzyko błędnego
  formatu.

### Negatywne / ryzyka

- własna implementacja musi pozostać zgodna ze specyfikacją samodzielnie
  (ryzyko pokryte testem z punktu 2);
- brak integracji z ekosystemem OTel (trace/metadata) do czasu rewizyty;
- dodatkowa odpowiedzialność utrzymania renderera w zespole.

### Rewizyta

Decyzja podlega wznowieniu, gdy pojawi się co najmniej jedna z potrzeb:

- trace/log/metric correlation (propagacja W3C `traceparent`);
- sampling i limit cardinality jako wymagane mechanizmy;
- eksport telemetrii do wielu backendów;
- wymóg interopu z narzędziami znającymi tylko OTLP.

Wtedy wykonuje się nowy ADR i wymianę silnika za portem.

### Migracja

Brak migracji — decyzja zatrzymuje obecną implementację. Działania:
dodać test zgodności z parserem referencyjnym w CI; utrwalić kontrakt
`observability.v1` (nazwy, HELP, etykiety, budżet kardynalności).