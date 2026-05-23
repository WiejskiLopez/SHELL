Najlepsza praktyka
Low-level
def repository():
    raise DatabaseError(...)

bez logowania.

Mid-level

opcjonalnie:

wrap exception,
dodaj kontekst.
try:
    repository()
except DatabaseError as exc:
    raise ServiceError("User loading failed") from exc
Top-level
try:
    app.run()
except Exception:
    logger.exception("Fatal application error")