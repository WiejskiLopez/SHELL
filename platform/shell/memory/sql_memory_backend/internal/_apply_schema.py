from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _apply_schema(backend: SqlMemoryBackend) -> None:
    dialect = backend.driver_.dialect_
    auto_pk = dialect.auto_pk_
    blob = dialect.blob_type_

    ddl = f"""
    CREATE TABLE IF NOT EXISTS context_entry (
        id              {auto_pk},
        context_type    TEXT NOT NULL,
        scope_id        TEXT NOT NULL,
        entry_key       TEXT NOT NULL,
        value_json      TEXT NOT NULL,
        tags            TEXT,
        created_at      TEXT NOT NULL,
        updated_at      TEXT NOT NULL,
        UNIQUE(context_type, scope_id, entry_key)
    );
    CREATE INDEX IF NOT EXISTS idx_ctx_type_scope ON context_entry(context_type, scope_id);
    CREATE INDEX IF NOT EXISTS idx_ctx_tags       ON context_entry(tags);

    CREATE TABLE IF NOT EXISTS session (
        session_id   TEXT PRIMARY KEY,
        agent_id     TEXT NOT NULL,
        goal         TEXT,
        status       TEXT NOT NULL,
        started_at   TEXT NOT NULL,
        ended_at     TEXT
    );

    CREATE TABLE IF NOT EXISTS message (
        id              {auto_pk},
        correlation_id  TEXT NOT NULL,
        sender          TEXT NOT NULL,
        receiver        TEXT NOT NULL,
        payload_json    TEXT NOT NULL,
        created_at      TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_msg_corr ON message(correlation_id);

    CREATE TABLE IF NOT EXISTS audit_event (
        id           {auto_pk},
        request_id   TEXT NOT NULL,
        trace_id     TEXT,
        "user"       TEXT,
        event_type   TEXT NOT NULL,
        payload_json TEXT,
        timestamp    TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_audit_req ON audit_event(request_id);

    CREATE TABLE IF NOT EXISTS rag_document (
        id          {auto_pk},
        source_uri  TEXT NOT NULL,
        title       TEXT,
        domain      TEXT,
        created_at  TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS rag_chunk (
        id              {auto_pk},
        document_id     INTEGER NOT NULL REFERENCES rag_document(id) ON DELETE CASCADE,
        chunk_index     INTEGER NOT NULL,
        chunk_text      TEXT NOT NULL,
        embedding       {blob},
        embedding_model TEXT,
        UNIQUE(document_id, chunk_index)
    );
    CREATE INDEX IF NOT EXISTS idx_chunk_doc ON rag_chunk(document_id);
    """
    backend.driver_.executescript(ddl)
    if dialect.supports_fts_:
        backend.driver_.executescript(
            "CREATE VIRTUAL TABLE IF NOT EXISTS rag_chunk_fts "
            "USING fts5(chunk_text, content='rag_chunk', content_rowid='id');"
        )
    backend.driver_.commit()
