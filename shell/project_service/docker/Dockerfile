FROM python:3.14-slim AS platform-builder
WORKDIR /build
ARG SOURCE_DATE_EPOCH=0
ENV SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH
COPY packaging/shell-platform/pyproject.toml ./pyproject.toml
COPY shell/platform ./shell/platform
RUN python -m pip wheel --no-cache-dir --no-deps --wheel-dir /dist .

FROM python:3.14-slim AS saga-orchestration-builder
WORKDIR /build
ARG SOURCE_DATE_EPOCH=0
ENV SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH
COPY packaging/saga-orchestration/pyproject.toml ./pyproject.toml
COPY packaging/saga-orchestration/saga_orchestration ./saga_orchestration
RUN python -m pip wheel --no-cache-dir --no-deps --wheel-dir /dist .

FROM python:3.14-slim AS project-service-builder
WORKDIR /build
ARG SOURCE_DATE_EPOCH=0
ENV SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH
COPY packaging/shell-project-service/pyproject.toml ./pyproject.toml
COPY shell/project_service ./shell/project_service
RUN python -m pip wheel --no-cache-dir --no-deps --wheel-dir /dist .

FROM python:3.14-slim AS certificate-builder
WORKDIR /certificates
ARG CERTIFICATE_BUILD_ID=local
COPY shell/certificates ./shell/certificates
COPY shell/certs/ca.crt shell/certs/ca.key ./ca/
RUN python -m pip install --no-cache-dir cryptography
RUN echo "certificate-build=$CERTIFICATE_BUILD_ID" && python -m shell.certificates issue --ca-dir /certificates/ca --output-dir /generated --name project --hostname shell-project-api

FROM python:3.14-slim
WORKDIR /app
COPY --from=platform-builder /dist /tmp/wheels
COPY --from=saga-orchestration-builder /dist /tmp/wheels
COPY --from=certificate-builder /generated/ca.crt /run/secrets/shell-mtls/ca.crt
COPY --from=certificate-builder /generated/project.crt /run/secrets/shell-mtls/project.crt
COPY --from=certificate-builder /generated/project.key /run/secrets/shell-mtls/project.key
COPY --from=project-service-builder /dist /tmp/wheels
RUN pip install --no-cache-dir /tmp/wheels/*.whl && rm -rf /tmp/wheels
ENV PYTHONUNBUFFERED=1
EXPOSE 8005
CMD ["python", "-m", "shell.project_service.bootstrap.project.main", "--host", "0.0.0", "--port", "8005"]
