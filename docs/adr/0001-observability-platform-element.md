# ADR-0001: Observability pozostaje elementem platformy

## Status

Accepted

## Data

2026-08-29

## Kontekst

W projekcie pojawiła się obserwowalność w dwóch formach:

- **Faktycznie zaimplementowane mechanizmy** żyją w platformie: kontrakty
  (`shell/platform/observability/application/ports/metrics.py`), rejestr metryk
  (`shell/platform/observability/infrastructure/metrics/registry.py`), backendy
  (`logging_metrics_backend.py`, `prometheus_metrics_backend.py`), middleware
  HTTP i endpoint `/metrics`, metryki inbound/outbound, readiness oraz
  dokumentacja Wiki (`shell/platform/doc/metrics.md`, `readiness.md`,
  `logging.md`, `tracing-context.md`).
- **Wprowadzono legacy artefakty** planistyczne: pusty moduł
  `shell/observability/` oraz `shell/platform/observability/` zawierające
  wyłącznie dokumenty `doc/TODO.md` opisujące "przyszłą zawartość" — bez żadnego
  kodu, portów, testów ani integracji w kontenerach.

Reguły projektu rozstrzygają o umiejscowieniu:

- `package-topology` — wspólne, generyczne, techniczne mechanizmy mieszkają
  wyłącznie w `shell/platform/`; nie istnieje współdzielony top-level
  `shell/observability`;
- `platform-boundary` — platforma może zawierać generyczne kontrakty i ich
  implementacje (logowanie, metryki, middleware, persistence lifecycle), ale
  nie importuje bc;
- `bounded-context-boundary` — mechanizmy techniczne mają jedną implementację
  w platformie i są używane przez wszystkie BC przez importy; nie ma
  niezależnego modułu obserwowalności jako drugiego domu technicznego.

Dodatkowo legacy koncept dokumentów `doc/TODO.md` (proza o przyszłej zawartości
w pustych katalogach) jest niezgodny z praktyką enterprise: plans i decyzji nie
utrwala się w drzewie kodu, tylko w Architecture Decision Records, a dokumentacja
katalogów opisuje stan zrealizowany.

## Decyzja

1. Observability jest i pozostaje **elementem platformy** — jej mechanizmy
   rozwijają się w `shell/platform/` (kontrakty, rejestr, backendy, middleware,
   endpoint, readiness, dokumentacja Wiki).
2. Usuwa się legacy artefakty: katalog `shell/observability/` oraz pusty
   szkielet `shell/platform/observability/` wraz z dokumentami `doc/TODO.md`.
3. Znosi się wzorzec plików `TODO.md`/"przyszłej zawartości" jako narzędzia
   planistycznego. Przyszłe zdolności planuje się przez ADR w `docs/adr/`
   (reguła utrwalona w skilu `adr-standard`).
4. Przyszłe rozszerzenia obserwowalności (np. pełny kontrakt `observability.v1`,
   limity cardinality, sampling, trace/log/metric correlation, redakcja danych)
   dokumentuje się w kolejnych ADR i implementuje w obrębie platformy, zgodnie
   z granicami płatvormy.

## Konsekwencje

- **Pozytywne:** jeden dom techniczny dla obserwowalności; brak duplikacji
  kontraktów i implementacji; granularność i wymienność backendów zachowana
  dzięki portom; dokumentacja opisuje wyłącznie realny stan.
- **Negatywne:** usunięta zalążkowa struktura nie niesie kodu do skasowania;
  ewentualna przyszła separacja obserwowalności na osobną zdolność (np.
  centralny collector/scraper) wymagałaby nowego ADR i realnego kodu z testami,
  a nie pustego szkieletu.
- **Migracja:** usunięcie pustych katalogów i dokumentów planu; aktualizacja
  skila dokumentacyjnego; dokumenty Wiki platformy pozostają bez zmian, bo
  opisują realnie działające mechanizmy.