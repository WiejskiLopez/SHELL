FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY shell/ ./shell/

RUN pip install --no-cache-dir -e . \
    && pip install --no-cache-dir uvicorn[standard] aiosqlite

ENV PYTHONUNBUFFERED=1

EXPOSE 8002

CMD ["python", "-m", "shell.definition.framework.definition.api", "--host", "0.0.0.0", "--port", "8002", "--db-url", "sqlite+aiosqlite:///shell_dev/definition.db"]
