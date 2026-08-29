# Badawczy CA i model certyfikatów mTLS (dev/research)

Ten katalog przechowuje **tymczasowy, badawczy CA** (`ca.crt` + `ca.key`).
To NIE jest sekret produkcyjny: CA żyje 5 lat, klucz prywatny CA jest potrzebny
**wyłącznie na maszynie budującej / w repo** (podpisuje certyfikaty). W produkcji
`ca.key` MUSI być chroniony (Vault/HSM) i nigdy w VCS — patrz
`docs/security/transport-security.md`.

## Model: certyfikat per obraz, mintowany w buildzie

- Każdy obraz ma **swój** certyfikat (per usługa), wygenerowany w buildzie
  przez stage `certificate-builder` (sign by CA), ważny **1 rok**.
- Do finalnego obrazu trafiają wyłącznie: `ca.crt` (publiczny), `.crt` i `.key`
  tej usługi → `/run/secrets/shell-mtls/`. **`ca.key` NIE jest w obrazie.**
- Certyfikat jest dwufunkcyjny (`SERVER_AUTH` + `CLIENT_AUTH`), a SAN pokrywa
  `<hostname>` + `localhost` + `127.0.0.1`.
- Obraz jest **samowystarczalny**: odpala się na dowolnym hoście z Dockerem bez
  dociągania certyfikatów.
- Świeży cert na każdą przebudowę: buduj z unikalnym `CERTIFICATE_BUILD_ID`
  (np. `docker build --build-arg CERTIFICATE_BUILD_ID=$(date +%s) ...`).

## Przygotowanie (tylko gdy chcesz CA w katalogu, np. dev)

```powershell
./scripts/generate_mtls_certs.py --output-dir shell/certs --force
# albo: .\.venv\Scripts\python.exe -m shell.certificates bundle --output-dir shell/certs
```

## Jak obraz używa certyfikatu

- Serwer (definition/session/execution): usługa startuje z TLS/mTLS, gdy ustawi
  się `{SERVICE}_SERVICE_TLS_CERTFILE=/run/secrets/shell-mtls/<svc>.crt`,
  `_KEYFILE`, `_CA_CERTS` i `_REQUIRE_CLIENT_CERT=true`.
- Klient (execution → definition/session): `{SERVICE}_SERVICE_MTLS_CA_CERTS/
  _CERTFILE/_KEYFILE` wskazują własny cert usługi (tożsamość per usługa).

Gotowy przykład deploymentu: `shell/mtls-demo/docker-compose.yml`.

## Ograniczenia tego badanego zestawu

- Weryfikacja tożsamości (CN) po stronie serwera — dalszy krok; klient prezentuje
  już osobną tożsamość per usługa.
- Brak automatycznej rotacji (bezpieczne do ~1 roku, potem odbudowa obrazu).
- CA i klucze lokalnie — w produkcji Vault/HSM + service mesh.
- mTLS obejmuje HTTP między usługami; broker (RabbitMQ) poza zakresem.