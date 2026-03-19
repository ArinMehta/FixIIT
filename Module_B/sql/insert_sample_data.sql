-- Module B Phase 2: sample auth data for existing members.
-- Passwords are SHA-256 hashes to match models.py verification logic.

USE fixiit_db;

INSERT INTO Credentials (member_id, username, password_hash)
VALUES
  (28, 'admin', SHA2('admin123', 256)),
  (2,  'user',  SHA2('user123', 256))
ON DUPLICATE KEY UPDATE
  username = VALUES(username),
  password_hash = VALUES(password_hash);
