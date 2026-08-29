# Podsumowanie — pozostałe prace i uwagi

Wykonane elementy zostały usunięte z tego dokumentu. Poniżej pozostają tylko
zadania, ryzyka i kwestie wymagające dalszej pracy.

## Do wykonania przed produkcją

1. **Uruchomienie obserwowalności na stagingu**
  - skonfigurować scrape Prometheusa, Alertmanager i Grafanę;
  - dostroić progi alertów i SLO na podstawie rzeczywistego ruchu;
  - potwierdzić alerty dla 5xx, p95, backlogu inbox/outbox, DLQ, wieku
    najstarszej wiadomości i otwartego circuit breakera.

2. **Docelowe uwierzytelnianie usług**
  - zastąpić API key service-tokenami JWT z `iss`, `aud`, `exp` i kluczem per
    usługa;
  - wdrożyć rotację sekretów oraz ich przechowywanie w Vault lub równoważnym
    systemie secrets management;
  - po migracji wyłączyć fallback do API key.

3. **TLS/mTLS**
  - przygotować realne CA i certyfikaty per usługa;
  - wdrożyć rotację certyfikatów i, jeśli będzie wymagana, wymuszać mTLS;
  - zweryfikować konfigurację w stagingu przed produkcją.

4. **Dodatkowa walidacja regresji**
  - uruchomić pełny `run_tests.ps1` w aktywnym środowisku `.venv`;
  - potwierdzić cross-service outbox/inbox oraz deserializację zdarzeń w
    scenariuszu rozproszonym;
  - utrzymać test izolacji modeli, rejestrów zdarzeń i niezależnego startu
    każdego serwisu.

## Uwagi i ryzyka

- TLS/mTLS jest przygotowane w kodzie, ale wymaga wdrożenia realnego CA,
  certyfikatów per usługa, rotacji i weryfikacji w stagingu.
- HMAC korzysta z sekretu powiązanego z API key. Chroni przed replayem w oknie
  300 sekund, ale nie zastępuje pełnego modelu tożsamości usług i rotacji kluczy.
- Metryki i dashboardy są artefaktami repozytorium, dopóki nie zostaną
  podłączone, przetestowane i skalibrowane w stagingu.

## Błędy i rozbieżności do sprawdzenia

- W bieżącej sesji bezpośrednie polecenie `pytest` nie zostało znalezione w
  `PATH`, więc deklaracja pełnej zielonej walidacji wymaga ponownego potwierdzenia
  przez `.venv\Scripts\python -m pytest` albo `run_tests.ps1`.
- Wcześniejsze opisy traktujące rejestry zdarzeń per BC jako brakujący blocker są
  nieaktualne: istnieją rejestry dla wszystkich siedmiu serwisów oraz test
  `shell/tests/architecture/test_event_registry_isolation.py`.

## Pozostały znany dług

- `scripts/find_syntax_error.py`, `scripts/option_pattern_refactor.py` — jednorazowe
  narzędzia dev (poza `mypy shell`).
- Wdrożenie/operacje: Prometheus scrape + Alertmanager + Grafana na stagingu,
  kalibracja SLO, migracja na service-tokeny, secrets w Vault i ewentualny
  service mesh (SPIFFE) — opisane w `docs/security/transport-security.md` i
  `docs/security/mtls-runbook.md`.

## Walidacja do ponowienia

- Uruchomić pełny `run_tests.ps1` w aktywnym środowisku `.venv`.
- Potwierdzić cross-service outbox/inbox oraz deserializację zdarzeń w
  scenariuszu rozproszonym.
- Utrzymać test izolacji modeli, rejestrów zdarzeń i niezależnego startu
  każdego serwisu.