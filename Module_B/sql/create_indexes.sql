-- Module B Phase 2 indexing strategy.
-- Indexes target frequent login and ticket dashboard filters.

USE fixiit_db;

-- Credentials table indexes (auth lookups).
CREATE INDEX idx_credentials_username ON Credentials(username);

-- Existing table indexes (API query patterns).
CREATE INDEX idx_tickets_member_id ON tickets(member_id);
CREATE INDEX idx_tickets_status_id ON tickets(status_id);
CREATE INDEX idx_member_roles_member_id ON member_roles(member_id);
CREATE INDEX idx_roles_role_code ON roles(role_code);
