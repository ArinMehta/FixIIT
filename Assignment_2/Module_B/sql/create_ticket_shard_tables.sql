-- Ticket shard schema.
-- Sharded tables intentionally avoid cross-shard foreign keys.

CREATE TABLE IF NOT EXISTS db_change_audit (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  table_name VARCHAR(100) NOT NULL,
  operation VARCHAR(10) NOT NULL,
  pk_value VARCHAR(100) NOT NULL,
  actor_member_id INT NULL,
  endpoint VARCHAR(255) NULL,
  source VARCHAR(20) NOT NULL,
  before_json JSON NULL,
  after_json JSON NULL,
  changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_db_change_audit_source_changed_at (source, changed_at),
  INDEX idx_db_change_audit_table_pk (table_name, pk_value)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tickets (
  ticket_id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(120) NOT NULL,
  description TEXT NOT NULL,
  member_id INT NOT NULL,
  location_id INT NOT NULL,
  category_id INT NOT NULL,
  priority VARCHAR(20) NOT NULL,
  status_id INT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT chk_ticket_priority
    CHECK (priority IN ('Low','Medium','High','Urgent','Emergency')),
  CHECK (created_at <= updated_at),
  INDEX idx_tickets_member_created_at (member_id, created_at),
  INDEX idx_tickets_created_at (created_at),
  INDEX idx_tickets_status_id (status_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
