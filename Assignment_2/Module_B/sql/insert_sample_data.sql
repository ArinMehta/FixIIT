-- Module B Phase 2: sample auth data for existing members.
-- Passwords are SHA-256 hashes to match models.py verification logic.

INSERT INTO Credentials (member_id, username, password_hash)
VALUES
  (28, 'admin', SHA2('admin123', 256)),
  (2,  'user',  SHA2('user123', 256))
ON DUPLICATE KEY UPDATE
  username = VALUES(username),
  password_hash = VALUES(password_hash);

INSERT INTO member_portfolio (member_id, bio, skills, github_url, linkedin_url)
VALUES
  (
    28,
    'Campus maintenance admin and system coordinator.',
    'Operations,incident-management,team-lead',
    'https://github.com/fixiit-admin',
    'https://linkedin.com/in/fixiit-admin'
  ),
  (
    2,
    'Student member interested in campus systems and maintenance workflows.',
    'reporting,documentation,frontend-basics',
    'https://github.com/fixiit-user',
    'https://linkedin.com/in/fixiit-user'
  )
ON DUPLICATE KEY UPDATE
  bio = VALUES(bio),
  skills = VALUES(skills),
  github_url = VALUES(github_url),
  linkedin_url = VALUES(linkedin_url),
  updated_at = CURRENT_TIMESTAMP;
