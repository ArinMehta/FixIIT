-- Module B Phase 2: create only the auth table needed for this module.
-- Existing project tables members, roles, member_roles are reused.

CREATE DATABASE IF NOT EXISTS fixiit_db
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE fixiit_db;

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
