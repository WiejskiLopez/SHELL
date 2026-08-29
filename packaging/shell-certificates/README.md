# shell-certificates

Shared certificate-generation infrastructure for SHELL research services.

Install the package and run `python -m shell.certificates ensure-ca --ca-dir <directory>` to create or reuse the five-year CA. During a Docker build, run `python -m shell.certificates issue --ca-dir <ca-directory> --output-dir <output-directory> --name <service> --hostname <service-hostname>` to issue a fresh service identity.

For this repository, run `scripts/prepare_mtls_ca.ps1` before building images.
The Dockerfiles copy the persistent CA into an intermediate builder and issue a
fresh service identity there. Pass a unique `--build-arg CERTIFICATE_BUILD_ID=...`
on every build to prevent Docker cache reuse for the certificate layer.
