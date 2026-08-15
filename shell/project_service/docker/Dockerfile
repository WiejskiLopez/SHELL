FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml ./
COPY shell/ ./shell/
RUN pip install --no-cache-dir -e . && pip install --no-cache-dir uvicorn[standard] aiosqlite
ENV PYTHONUNBUFFERED=1
EXPOSE 8005
CMD ["python", "-m", "shell.project_service.bootstrap.project.main", "--host", "0.0.0.0", "--port", "8005", "--db-url", "sqlite+aiosqlite:///shell_dev/project.db"]
