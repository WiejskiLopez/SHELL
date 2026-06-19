-- Schema dump for SQLite — porównanie z modelami/migracjami
-- Uruchom: sqlite3 shell.db < schema_dump.sql

.print '========================================'
.print '1. Tabele i ich kolumny'
.print '========================================'

SELECT
    m.name AS table_name,
    p.cid AS column_id,
    p.name AS column_name,
    p.type AS column_type,
    CASE p."notnull" WHEN 0 THEN 'YES' ELSE 'NO' END AS nullable,
    COALESCE(p.dflt_value, '') AS default_value,
    CASE p.pk WHEN 1 THEN 'YES' ELSE '' END AS is_pk
FROM sqlite_master AS m
JOIN pragma_table_info(m.name) AS p
WHERE m.type = 'table'
  AND m.name NOT LIKE 'sqlite_%'
  AND m.name NOT LIKE 'alembic_%'
ORDER BY m.name, p.cid;

.print ''
.print '========================================'
.print '2. Indeksy'
.print '========================================'

SELECT
    m.name AS table_name,
    ix.name AS index_name,
    CASE ix."unique" WHEN 1 THEN 'YES' ELSE 'NO' END AS unique_index,
    GROUP_CONCAT(ii.name, ', ') AS indexed_columns
FROM sqlite_master AS m
JOIN pragma_index_list(m.name) AS ix ON m.name = ix."table"
JOIN pragma_index_info(ix.name) AS ii
WHERE m.type = 'table'
  AND m.name NOT LIKE 'sqlite_%'
  AND m.name NOT LIKE 'alembic_%'
  AND ix.name NOT LIKE 'sqlite_autoindex_%'
GROUP BY m.name, ix.name, ix."unique"
ORDER BY m.name, ix.name;

.print ''
.print '========================================'
.print '3. Klucze obce'
.print '========================================'

SELECT
    m.name AS table_name,
    f.id AS fk_id,
    f.seq AS fk_seq,
    f."table" AS referenced_table,
    f.from AS from_column,
    f.to AS to_column,
    f.on_update,
    f.on_delete
FROM sqlite_master AS m
JOIN pragma_foreign_key_list(m.name) AS f
WHERE m.type = 'table'
  AND m.name NOT LIKE 'sqlite_%'
  AND m.name NOT LIKE 'alembic_%'
ORDER BY m.name, f.id, f.seq;

.print ''
.print '========================================'
.print '4. Liczby rekordów'
.print '========================================'

SELECT
    m.name AS table_name,
    (SELECT COUNT(*) FROM pragma_table_info(m.name)) AS column_count,
    (SELECT COUNT(*) FROM pragma_index_list(m.name)
     WHERE name NOT LIKE 'sqlite_autoindex_%') AS index_count,
    (SELECT COUNT(*) FROM pragma_foreign_key_list(m.name)) AS fk_count
FROM sqlite_master AS m
WHERE m.type = 'table'
  AND m.name NOT LIKE 'sqlite_%'
  AND m.name NOT LIKE 'alembic_%'
ORDER BY m.name;

.print ''
.print '========================================'
.print '5. DDL wszystkich tabel (CREATE TABLE)'
.print '========================================'

SELECT
    m.name AS table_name,
    m.sql AS ddl
FROM sqlite_master AS m
WHERE m.type = 'table'
  AND m.name NOT LIKE 'sqlite_%'
  AND m.name NOT LIKE 'alembic_%'
ORDER BY m.name;

.print ''
.print '========================================'
.print '6. DDL wszystkich indeksów (CREATE INDEX)'
.print '========================================'

SELECT
    m.name AS index_name,
    m.sql AS ddl
FROM sqlite_master AS m
WHERE m.type = 'index'
  AND m.name NOT LIKE 'sqlite_autoindex_%'
  AND m.sql IS NOT NULL
ORDER BY m.name;
