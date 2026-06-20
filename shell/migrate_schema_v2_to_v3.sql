-- Schema migration: align SQLite DB with current Python SQLAlchemy models
-- SQLite 3.50.4 supports ALTER TABLE DROP COLUMN (requires 3.35.0+)

-- ============================================================
-- 1. task_execution: add workflow_id (new field for Workflow → N TaskExecution)
-- ============================================================
ALTER TABLE task_execution ADD COLUMN workflow_id VARCHAR(36);
CREATE INDEX IF NOT EXISTS ix_task_execution_workflow_id ON task_execution (workflow_id);

-- ============================================================
-- 2. graph_execution: add workflow_id (new field for direct workflow lookup)
-- ============================================================
ALTER TABLE graph_execution ADD COLUMN workflow_id VARCHAR(255);
CREATE INDEX IF NOT EXISTS ix_graph_execution_workflow_id ON graph_execution (workflow_id);

-- ============================================================
-- 3. graph_execution: remove unique constraint on task_execution_id
--    (1 TaskExecution → N GraphExecutions, not 1:1)
-- ============================================================
DROP INDEX IF EXISTS uq_graph_execution_task_execution_id;

-- ============================================================
-- 4. graph_execution: remove deprecated parent_tasker_node_execution_id
--    (removed from domain model — CrownScheduler tracks parent/child)
-- ============================================================
DROP INDEX IF EXISTS ix_graph_execution_parent_tasker_node_execution_id;
ALTER TABLE graph_execution DROP COLUMN parent_tasker_node_execution_id;

-- ============================================================
-- 5. workflow: remove deprecated task_execution_id
--    (no longer — TaskExecution.workflow_id is the FK direction)
--    Keep the column for backward compat with existing data
--    (optional: uncomment to drop)
-- ============================================================
-- DROP INDEX IF EXISTS ix_workflow_task_execution_id;
-- ALTER TABLE workflow DROP COLUMN task_execution_id;

-- ============================================================
-- 6. Update default values to match models
--    (SQLite cannot ALTER DEFAULT; these only affect NEW rows
--     when using INSERT without explicit value)
-- ============================================================
-- task_execution.status: DB has 'PENDING', model has 'CREATED'
-- graph_execution.status: DB has 'RUNNING', model has 'CREATED'
-- These are cosmetic and do not affect existing data.

-- ============================================================
-- Verify
-- ============================================================
SELECT '=== migration complete ===' AS status;
SELECT 'task_execution columns:' AS info;
PRAGMA table_info(task_execution);
SELECT 'graph_execution columns:' AS info;
PRAGMA table_info(graph_execution);
SELECT 'workflow columns:' AS info;
PRAGMA table_info(workflow);
SELECT 'indexes:' AS info;
SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name IN ('task_execution', 'graph_execution', 'workflow') ORDER BY name;
