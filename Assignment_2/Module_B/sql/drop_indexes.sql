-- Module B Phase 3: drop indexing layer for baseline benchmarking
-- and remove legacy redundant indexes.

USE fixiit_db;

SET @db_name := DATABASE();

-- Drop index helper (safe: only executes when index exists)
SET @idx_exists := (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = @db_name
      AND table_name = 'tickets'
      AND index_name = 'idx_tickets_member_created_at'
);
SET @sql := IF(@idx_exists > 0, 'DROP INDEX idx_tickets_member_created_at ON tickets', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_exists := (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = @db_name
      AND table_name = 'tickets'
      AND index_name = 'idx_tickets_created_at'
);
SET @sql := IF(@idx_exists > 0, 'DROP INDEX idx_tickets_created_at ON tickets', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Legacy indexes from earlier draft (drop if present)
SET @idx_exists := (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = @db_name
      AND table_name = 'tickets'
      AND index_name = 'idx_tickets_member_id'
);
SET @sql := IF(@idx_exists > 0, 'DROP INDEX idx_tickets_member_id ON tickets', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_exists := (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = @db_name
      AND table_name = 'tickets'
      AND index_name = 'idx_tickets_status_id'
);
SET @sql := IF(@idx_exists > 0, 'DROP INDEX idx_tickets_status_id ON tickets', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_exists := (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = @db_name
      AND table_name = 'member_roles'
      AND index_name = 'idx_member_roles_member_id'
);
SET @sql := IF(@idx_exists > 0, 'DROP INDEX idx_member_roles_member_id ON member_roles', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_exists := (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = @db_name
      AND table_name = 'roles'
      AND index_name = 'idx_roles_role_code'
);
SET @sql := IF(@idx_exists > 0, 'DROP INDEX idx_roles_role_code ON roles', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_exists := (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = @db_name
      AND table_name = 'Credentials'
      AND index_name = 'idx_credentials_username'
);
SET @sql := IF(@idx_exists > 0, 'DROP INDEX idx_credentials_username ON Credentials', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
