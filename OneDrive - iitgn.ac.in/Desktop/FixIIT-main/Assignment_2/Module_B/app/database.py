"""Database utility layer for Module B.

This module keeps SQL access simple and explicit.
It uses the existing FixIIT tables:
- members
- roles
- member_roles
And the new Credentials table.
"""

import mysql.connector
from mysql.connector import Error

from config import DB_CONFIG


class DatabaseError(Exception):
    """Raised when a database operation fails."""


def get_connection():
    """Create and return a new MySQL connection."""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as exc:
        raise DatabaseError(f"Could not connect to database: {exc}") from exc


def fetch_one(query, params=None):
    """Run a SELECT query and return one row as a dict, or None."""
    connection = get_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()
    except Error as exc:
        raise DatabaseError(f"Query failed: {exc}") from exc
    finally:
        connection.close()


def fetch_all(query, params=None):
    """Run a SELECT query and return all rows as a list of dicts."""
    connection = get_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()
    except Error as exc:
        raise DatabaseError(f"Query failed: {exc}") from exc
    finally:
        connection.close()


def execute_write(query, params=None, audit_context=None):
    """Run INSERT/UPDATE/DELETE and return affected row count.

    Optional audit_context shape:
        {
            "actor_member_id": <int_or_none>,
            "endpoint": "<route_or_action_name>"
        }
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
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

            cursor.execute(query, params or ())
            connection.commit()
            return cursor.rowcount
    except Error as exc:
        connection.rollback()
        raise DatabaseError(f"Write query failed: {exc}") from exc
    finally:
        connection.close()


def get_member_auth_record(username):
    """Fetch member profile + credential + roles by username.

    This join is the main bridge between new auth data (Credentials)
    and existing FixIIT member data (members/member_roles/roles).
    """
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
    """Create Module B tables if they do not exist.

    This makes local development resilient when setup SQL scripts have not
    been run manually yet.
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
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
                """
            )

            cursor.execute(
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
                """
            )

        connection.commit()
    except Error as exc:
        connection.rollback()
        raise DatabaseError(f"Initialization failed: {exc}") from exc
    finally:
        connection.close()
