-- ====================================================================
-- sync_db_schema.sql
-- Aligns the SQLite database schema with the application's ORM models
-- by applying the missing Alembic migrations 021 -> 024.
--
-- Usage:
--   sqlite3 shell.db < sync_db_schema.sql
-- or within an open connection:
--   .read sync_db_schema.sql
--
-- WARNING:
--   * graph_execution_state will be DROPPED (data lost) and replaced
--     by two empty tables (graph_execution_state_input / _output).
--   * Run against a DB that is at migration level ~018-020.
--   * Do NOT run twice — ALTER TABLE RENAME will fail the second time.
-- ====================================================================

-- Temporarily disable FK enforcement so destructive DDL can run
PRAGMA foreign_keys = OFF;

-- ====================================================================
-- 1. Migration 021: Remove obsolete columns
-- ====================================================================

-- graph_execution: drop parent_tasker_node_execution_id + its index
DROP INDEX IF EXISTS ix_graph_execution_parent_tasker_node_execution_id;
ALTER TABLE graph_execution DROP COLUMN parent_tasker_node_execution_id;

-- graph_node_definition: drop extra
ALTER TABLE graph_node_definition DROP COLUMN extra;

-- graph_node_execution: drop 3 obsolete columns
ALTER TABLE graph_node_execution DROP COLUMN extra;
ALTER TABLE graph_node_execution DROP COLUMN sub_graph_definition_id;
ALTER TABLE graph_node_execution DROP COLUMN sub_graph_definition_version;

-- ====================================================================
-- 2. Migration 022: Split graph_execution_state into input / output
-- ====================================================================

CREATE TABLE graph_execution_state_input (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    graph_execution_id VARCHAR(36) NOT NULL REFERENCES graph_execution(id) ON DELETE CASCADE,
    payload JSON NOT NULL DEFAULT '{}',
    is_current BOOLEAN NOT NULL DEFAULT true,
    created_at DATETIME NOT NULL
);

CREATE INDEX ix_graph_execution_state_input_graph_execution_id
    ON graph_execution_state_input(graph_execution_id);

CREATE UNIQUE INDEX uq_graph_execution_state_input_is_current
    ON graph_execution_state_input(graph_execution_id)
    WHERE is_current = 1;

CREATE TABLE graph_execution_state_output (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    graph_execution_id VARCHAR(36) NOT NULL REFERENCES graph_execution(id) ON DELETE CASCADE,
    payload JSON NOT NULL DEFAULT '{}',
    is_current BOOLEAN NOT NULL DEFAULT true,
    created_at DATETIME NOT NULL
);

CREATE INDEX ix_graph_execution_state_output_graph_execution_id
    ON graph_execution_state_output(graph_execution_id);

CREATE UNIQUE INDEX uq_graph_execution_state_output_is_current
    ON graph_execution_state_output(graph_execution_id)
    WHERE is_current = 1;

-- Drop old graph_execution_state table and its indexes
DROP INDEX IF EXISTS uq_graph_execution_state_is_current;
DROP INDEX IF EXISTS ix_graph_execution_state_graph_execution_id;
DROP TABLE IF EXISTS graph_execution_state;

-- ====================================================================
-- 3. Migration 023: Rename node payload tables
-- ====================================================================

ALTER TABLE graph_node_execution_input_payload RENAME TO graph_node_execution_state_input;
ALTER TABLE graph_node_execution_output_payload RENAME TO graph_node_execution_state_output;

-- Create indexes with new names, then drop old-named ones
CREATE INDEX IF NOT EXISTS ix_graph_node_execution_state_input_graph_node_execution_id
    ON graph_node_execution_state_input(graph_node_execution_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_graph_node_execution_state_input_is_current
    ON graph_node_execution_state_input(graph_node_execution_id)
    WHERE is_current = 1;
DROP INDEX IF EXISTS ix_graph_node_execution_input_payload_graph_node_execution_id;
DROP INDEX IF EXISTS uq_graph_node_execution_input_payload_is_current;

CREATE INDEX IF NOT EXISTS ix_graph_node_execution_state_output_graph_node_execution_id
    ON graph_node_execution_state_output(graph_node_execution_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_graph_node_execution_state_output_is_current
    ON graph_node_execution_state_output(graph_node_execution_id)
    WHERE is_current = 1;
DROP INDEX IF EXISTS ix_graph_node_execution_output_payload_graph_node_execution_id;
DROP INDEX IF EXISTS uq_graph_node_execution_output_payload_is_current;

-- ====================================================================
-- 4. Migration 024: Rename task payload tables
-- ====================================================================

ALTER TABLE task_execution_input_payload RENAME TO task_execution_state_input;
ALTER TABLE task_execution_output_payload RENAME TO task_execution_state_output;

CREATE INDEX IF NOT EXISTS ix_task_execution_state_input_task_execution_id
    ON task_execution_state_input(task_execution_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_task_execution_state_input_is_current
    ON task_execution_state_input(task_execution_id)
    WHERE is_current = 1;
DROP INDEX IF EXISTS ix_task_execution_input_payload_task_execution_id;
DROP INDEX IF EXISTS uq_task_execution_input_payload_is_current;

CREATE INDEX IF NOT EXISTS ix_task_execution_state_output_task_execution_id
    ON task_execution_state_output(task_execution_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_task_execution_state_output_is_current
    ON task_execution_state_output(task_execution_id)
    WHERE is_current = 1;
DROP INDEX IF EXISTS ix_task_execution_output_payload_task_execution_id;
DROP INDEX IF EXISTS uq_task_execution_output_payload_is_current;

-- ====================================================================
-- Done -- re-enable FK enforcement
-- ====================================================================

PRAGMA foreign_keys = ON;
