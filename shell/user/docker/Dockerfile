FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY shell/ ./shell/

RUN pip install --no-cache-dir -e . \
    && pip install --no-cache-dir uvicorn[standard] aiosqlite

ENV PYTHONUNBUFFERED=1

EXPOSE 8001

CMD ["python", "-m", "shell.user.bootstrap.user.main", "--host", "0.0.0.0", "--port", "8001", "--db-url", "sqlite+aiosqlite:///shell_dev/user.db", "--api-key", "dev-user-key"]
