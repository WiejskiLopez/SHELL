# ADR-0003: Shared SQL Adapters for SQLite and PostgreSQL

**Date:** 2025-01  
**Status:** Accepted

## Context

The old SHELL had two separate SQL drivers (`SqliteDriver`, `PostgresDriver`) that duplicated
repository code.  The new design must support both dialects without duplication.

## Decision

`shell` uses a **single set of SQLAlchemy 2.x async ORM models and repositories** located in
`infrastructure/persistence/sql/`.  Dialect is selected at runtime by the `database_url` string:

- `sqlite+aiosqlite://...` → aiosqlite engine
- `postgresql+asyncpg://...` → asyncpg engine

The `build_session_factory(url)` helper in `infrastructure/persistence/sql/__init__.py`
creates the correct `AsyncEngine` and returns an `async_sessionmaker`.

## Rationale

1. SQLAlchemy abstracts dialect differences at the ORM level; column types like `JSON` work on both.
2. Dialect-specific Alembic migration scripts live in `migrations/sql/versions/` and use
   `op.get_context().dialect.name` for any per-dialect DDL differences.
3. PostgreSQL uses `asyncpg`; SQLite uses `aiosqlite` — both are async-native, matching the
   fully-async application layer.

## Consequences

- Adding a new DB column requires one Alembic migration that covers both dialects.
- MongoDB is a separate adapter tree (`infrastructure/persistence/mongo/`) and is not shared.
- Tests run against SQLite by default; CI optionally starts Postgres+Mongo via `docker-compose.test.yml`.
