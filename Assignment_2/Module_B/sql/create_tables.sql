-- Module B coordinator schema.
-- Existing project tables members, roles, member_roles, categories, locations,
-- and statuses remain authoritative in the coordinator database.

CREATE TABLE IF NOT EXISTS Credentials (
  member_id INT NOT NULL,
  username VARCHAR(80) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (member_id),
  UNIQUE KEY uk_credentials_username (username),
  CONSTRAINT fk_credentials_member
    FOREIGN KEY (member_id) REFERENCES members(member_id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS member_portfolio (
  member_id INT NOT NULL,
  bio TEXT NULL,
  skills VARCHAR(500) NULL,
  github_url VARCHAR(255) NULL,
  linkedin_url VARCHAR(255) NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (member_id),
  CONSTRAINT fk_member_portfolio_member
    FOREIGN KEY (member_id) REFERENCES members(member_id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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

CREATE TABLE IF NOT EXISTS ticket_locator (
  ticket_id INT NOT NULL,
  member_id INT NOT NULL,
  shard_idx TINYINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (ticket_id),
  KEY idx_ticket_locator_member_id (member_id),
  KEY idx_ticket_locator_shard_idx (shard_idx),
  CONSTRAINT chk_ticket_locator_shard_idx CHECK (shard_idx BETWEEN 0 AND 2),
  CONSTRAINT fk_ticket_locator_member
    FOREIGN KEY (member_id) REFERENCES members(member_id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ticket_id_allocator (
  ticket_id INT AUTO_INCREMENT PRIMARY KEY,
  allocated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS migration_state (
  migration_name VARCHAR(100) NOT NULL,
  completed_at DATETIME NOT NULL,
  PRIMARY KEY (migration_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
