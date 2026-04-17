"""Database utility layer for Module B."""

from pathlib import Path

import mysql.connector
from mysql.connector import Error

from config import COORDINATOR_DB_CONFIG, TICKET_SHARD_CONFIGS


class DatabaseError(Exception):
    """Raised when a database operation fails."""


def _resolved_config(db_config=None):
    """Return the coordinator config unless an explicit config is passed."""
    return (db_config or COORDINATOR_DB_CONFIG).copy()


def _config_without_database(db_config):
    """Return a MySQL config usable for CREATE DATABASE calls."""
    config = _resolved_config(db_config)
    config.pop("database", None)
    return config


def get_connection(db_config=None, include_database=True):
    """Create and return a new MySQL connection."""
    config = _resolved_config(db_config)
    if not include_database:
        config.pop("database", None)

    try:
        return mysql.connector.connect(**config)
    except Error as exc:
        raise DatabaseError(f"Could not connect to database: {exc}") from exc


def _set_audit_context(cursor, audit_context):
    """Bind app-level audit context for DB triggers on the current connection."""
    if audit_context:
        cursor.execute(
            "SET @app_actor_member_id = %s, @app_endpoint = %s",
            (
                audit_context.get("actor_member_id"),
                audit_context.get("endpoint"),
            ),
        )
    else:
        cursor.execute("SET @app_actor_member_id = NULL, @app_endpoint = NULL")


def fetch_one(query, params=None, db_config=None):
    """Run a SELECT query and return one row as a dict, or None."""
    connection = get_connection(db_config=db_config)
    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()
    except Error as exc:
        raise DatabaseError(f"Query failed: {exc}") from exc
    finally:
        connection.close()


def fetch_all(query, params=None, db_config=None):
    """Run a SELECT query and return all rows as a list of dicts."""
    connection = get_connection(db_config=db_config)
    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()
    except Error as exc:
        raise DatabaseError(f"Query failed: {exc}") from exc
    finally:
        connection.close()


def execute_write(query, params=None, audit_context=None, db_config=None):
    """Run INSERT/UPDATE/DELETE and return affected row count."""
    connection = get_connection(db_config=db_config)
    try:
        with connection.cursor() as cursor:
            _set_audit_context(cursor, audit_context)
            cursor.execute(query, params or ())
            connection.commit()
            return cursor.rowcount
    except Error as exc:
        connection.rollback()
        raise DatabaseError(f"Write query failed: {exc}") from exc
    finally:
        connection.close()


def execute_insert(query, params=None, audit_context=None, db_config=None):
    """Run INSERT and return the new lastrowid plus affected row count."""
    connection = get_connection(db_config=db_config)
    try:
        with connection.cursor() as cursor:
            _set_audit_context(cursor, audit_context)
            cursor.execute(query, params or ())
            connection.commit()
            return {
                "rowcount": cursor.rowcount,
                "lastrowid": cursor.lastrowid,
            }
    except Error as exc:
        connection.rollback()
        raise DatabaseError(f"Insert query failed: {exc}") from exc
    finally:
        connection.close()


def allocate_ticket_id():
    """Allocate the next globally unique ticket_id from the coordinator DB."""
    result = execute_insert(
        """
        INSERT INTO ticket_id_allocator (allocated_at)
        VALUES (NOW())
        """
    )
    ticket_id = result.get("lastrowid")
    if not ticket_id:
        raise DatabaseError("Global ticket_id allocation failed")
    return int(ticket_id)


def get_next_ticket_id_allocator_value():
    """Return the next ticket_id that the coordinator allocator would issue."""
    row = fetch_one(
        """
        SELECT COALESCE(MAX(ticket_id), 0) + 1 AS next_ticket_id
        FROM ticket_id_allocator
        """
    )
    return int(row["next_ticket_id"])


def advance_ticket_id_allocator(min_next_ticket_id):
    """Ensure the coordinator allocator will issue at least the given next id."""
    current_next_ticket_id = get_next_ticket_id_allocator_value()
    target_next_ticket_id = max(int(min_next_ticket_id), current_next_ticket_id)
    execute_write(f"ALTER TABLE ticket_id_allocator AUTO_INCREMENT = {target_next_ticket_id}")
    return target_next_ticket_id


def is_ticket_sharding_migration_complete():
    """Return whether the Assignment 4 ticket sharding migration has completed."""
    row = fetch_one(
        """
        SELECT completed_at
        FROM migration_state
        WHERE migration_name = 'assignment4_ticket_sharding'
        """
    )
    return bool(row and row.get("completed_at"))


def mark_ticket_sharding_migration_complete():
    """Record successful completion of the Assignment 4 ticket sharding migration."""
    execute_write(
        """
        INSERT INTO migration_state (migration_name, completed_at)
        VALUES ('assignment4_ticket_sharding', NOW())
        ON DUPLICATE KEY UPDATE
            completed_at = VALUES(completed_at)
        """
    )


def ensure_database_exists(db_config):
    """Create the configured database if it does not already exist."""
    config = _resolved_config(db_config)
    database_name = config["database"]
    connection = get_connection(db_config=_config_without_database(db_config), include_database=False)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                CREATE DATABASE IF NOT EXISTS `{database_name}`
                  DEFAULT CHARACTER SET utf8mb4
                  DEFAULT COLLATE utf8mb4_unicode_ci
                """
            )
        connection.commit()
    except Error as exc:
        connection.rollback()
        raise DatabaseError(f"Failed to create database {database_name}: {exc}") from exc
    finally:
        connection.close()


def execute_sql_script(script_path, db_config=None):
    """Execute a SQL script file, including scripts that change DELIMITER."""
    script_text = Path(script_path).read_text(encoding="utf-8")
    statements = []
    delimiter = ";"
    chunk = []

    for raw_line in script_text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("--"):
            continue

        if stripped.upper().startswith("DELIMITER "):
            delimiter = stripped.split(None, 1)[1]
            continue

        chunk.append(raw_line)
        if raw_line.rstrip().endswith(delimiter):
            statement = "\n".join(chunk).rstrip()
            statements.append(statement[: -len(delimiter)].strip())
            chunk = []

    if chunk:
        trailing = "\n".join(chunk).strip()
        if trailing:
            statements.append(trailing)

    connection = get_connection(db_config=db_config)
    try:
        with connection.cursor() as cursor:
            for statement in statements:
                if statement:
                    cursor.execute(statement)
        connection.commit()
    except Error as exc:
        connection.rollback()
        raise DatabaseError(f"Failed to execute SQL script {script_path}: {exc}") from exc
    finally:
        connection.close()


def member_exists(member_id):
    """Check whether a member exists in the coordinator DB."""
    row = fetch_one("SELECT 1 AS found FROM members WHERE member_id = %s", (member_id,))
    return bool(row)


def location_exists(location_id):
    """Check whether a location exists in the coordinator DB."""
    row = fetch_one("SELECT 1 AS found FROM locations WHERE location_id = %s", (location_id,))
    return bool(row)


def category_exists(category_id):
    """Check whether a category exists in the coordinator DB."""
    row = fetch_one("SELECT 1 AS found FROM categories WHERE category_id = %s", (category_id,))
    return bool(row)


def status_exists(status_id):
    """Check whether a status exists in the coordinator DB."""
    row = fetch_one("SELECT 1 AS found FROM statuses WHERE status_id = %s", (status_id,))
    return bool(row)


def get_member_auth_record(username):
    """Fetch member profile + credential + roles by username."""
    query = """
        SELECT
            m.member_id,
            m.name,
            m.email,
            m.contact_number,
            m.address,
            c.username,
            c.password_hash,
            GROUP_CONCAT(DISTINCT r.role_code ORDER BY r.role_code) AS role_codes
        FROM Credentials c
        JOIN members m
          ON m.member_id = c.member_id
        LEFT JOIN member_roles mr
          ON mr.member_id = m.member_id
        LEFT JOIN roles r
          ON r.role_id = mr.role_id
        WHERE c.username = %s
        GROUP BY
            m.member_id,
            m.name,
            m.email,
            m.contact_number,
            m.address,
            c.username,
            c.password_hash
    """
    return fetch_one(query, (username,))


def get_member_by_id(member_id):
    """Return basic member data from members table by member_id."""
    query = """
        SELECT
            member_id,
            name,
            email,
            contact_number,
            address
        FROM members
        WHERE member_id = %s
    """
    return fetch_one(query, (member_id,))


def is_member_admin(member_id):
    """Check admin status using existing member_roles + roles tables."""
    query = """
        SELECT 1 AS is_admin
        FROM member_roles mr
        JOIN roles r
          ON r.role_id = mr.role_id
        WHERE mr.member_id = %s
          AND UPPER(r.role_code) = 'ADMIN'
        LIMIT 1
    """
    row = fetch_one(query, (member_id,))
    return bool(row)


def create_credentials(member_id, username, password_hash):
    """Create one credentials row for an existing member."""
    query = """
        INSERT INTO Credentials (member_id, username, password_hash)
        VALUES (%s, %s, %s)
    """
    return execute_write(query, (member_id, username, password_hash))


def initialize_module_b_tables():
    """Create coordinator and shard tables needed by Module B."""
    coordinator_ddls = [
        """
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS ticket_id_allocator (
          ticket_id INT AUTO_INCREMENT PRIMARY KEY,
          allocated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS migration_state (
          migration_name VARCHAR(100) NOT NULL,
          completed_at DATETIME NOT NULL,
          PRIMARY KEY (migration_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
    ]
    shard_ddls = [
        """
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
    ]

    try:
        ensure_database_exists(COORDINATOR_DB_CONFIG)
        for shard_config in TICKET_SHARD_CONFIGS.values():
            ensure_database_exists(shard_config)

        coordinator_connection = get_connection()
        try:
            with coordinator_connection.cursor() as cursor:
                for ddl in coordinator_ddls:
                    cursor.execute(ddl)
            coordinator_connection.commit()
        except Error as exc:
            coordinator_connection.rollback()
            raise DatabaseError(f"Coordinator initialization failed: {exc}") from exc
        finally:
            coordinator_connection.close()

        for shard_config in TICKET_SHARD_CONFIGS.values():
            shard_connection = get_connection(db_config=shard_config)
            try:
                with shard_connection.cursor() as cursor:
                    for ddl in shard_ddls:
                        cursor.execute(ddl)
                shard_connection.commit()
            except Error as exc:
                shard_connection.rollback()
                raise DatabaseError(f"Shard initialization failed: {exc}") from exc
            finally:
                shard_connection.close()
    except Error as exc:
        raise DatabaseError(f"Initialization failed: {exc}") from exc
