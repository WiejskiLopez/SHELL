Jak używać Memory
1. Inicjalizacja
Aby przejść na inną bazę — wstrzykujesz inny driver, np. PostgresDriver(dsn) (gdy stub zostanie dokończony). Reszta kodu się nie zmienia.

2. Context entries (klucz–wartość per scope)
context_type to typ kontekstu (system, domain, session, memory, state, audit, execution, communication).

3. Sesje agentów
4. Konwersacje (komunikacja między agentami)
5. Audit log
6. RAG (przez memory.rag_)
7. Zamknięcie
Ścieżka skrótu — gdzie co siedzi
memory.put_entry/get_entry/... — context_entry (UPSERT po (context_type, scope_id, entry_key))
memory.open_session/close_session — tabela session
memory.append_message/get_conversation — tabela message (po correlation_id)
memory.log_event — tabela audit_event
memory.rag_.index_text — tabele rag_document + rag_chunk (+ rag_chunk_fts na sqlite)
memory.rag_.search — kosinusowe podobieństwo embeddingów w Pythonie
memory.backend_.search_fts — BM25 przez FTS5
Aby podpiąć prawdziwe embeddingi (np. OpenAI / sentence-transformers) — zaimplementuj Embedder (jeden metod encode(text) -> list[float]) zamiast HashEmbedder.