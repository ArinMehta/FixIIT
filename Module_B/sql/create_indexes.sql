-- Module B Phase 3 indexing strategy.
-- Keep only indexes that match real API query patterns.
-- Auth and RBAC already use existing UNIQUE/PK-backed indexes:
--   - Credentials.username (uk_credentials_username)
--   - roles.role_code (UNIQUE)
--   - member_roles(member_id, role_id) (UNIQUE composite)

USE fixiit_db;

-- Query pattern:
--   GET /tickets -> WHERE member_id = ? ORDER BY created_at DESC
-- Best index: composite filter + sort.
SET @db_name := DATABASE();
SET @idx_exists := (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = @db_name
      AND table_name = 'tickets'
      AND index_name = 'idx_tickets_member_created_at'
);
SET @sql := IF(
    @idx_exists = 0,
    'CREATE INDEX idx_tickets_member_created_at ON tickets(member_id, created_at)',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Query pattern:
--   GET /admin/tickets -> ORDER BY created_at DESC
SET @idx_exists := (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = @db_name
      AND table_name = 'tickets'
      AND index_name = 'idx_tickets_created_at'
);
SET @sql := IF(
    @idx_exists = 0,
    'CREATE INDEX idx_tickets_created_at ON tickets(created_at)',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
