"""Utilities for loading monolithic ticket source data for migration checks."""

from ast import literal_eval
from pathlib import Path
import re

from mysql.connector import Error, errorcode

from app.database import DatabaseError, get_connection
from config import LEGACY_TICKET_SOURCE_DB_CONFIG, SOURCE_TICKET_SQL_PATH


SOURCE_TICKET_COLUMNS = [
    "ticket_id",
    "title",
    "description",
    "member_id",
    "location_id",
    "category_id",
    "priority",
    "status_id",
    "created_at",
    "updated_at",
]


def _load_tickets_from_db():
    """Load source tickets from the configured legacy monolith DB if present."""
    connection = None
    try:
        connection = get_connection(db_config=LEGACY_TICKET_SOURCE_DB_CONFIG)
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT
                    ticket_id,
                    title,
                    description,
                    member_id,
                    location_id,
                    category_id,
                    priority,
                    status_id,
                    created_at,
                    updated_at
                FROM tickets
                ORDER BY ticket_id
                """
            )
            return cursor.fetchall()
    except Error as exc:
        if exc.errno == errorcode.ER_NO_SUCH_TABLE:
            return None
        raise DatabaseError(
            f"Legacy ticket source DB is configured but could not be read safely: {exc}"
        ) from exc
    finally:
        if connection is not None:
            connection.close()


def _load_tickets_from_sql_seed():
    """Parse the Track1 SQL seed file as a fallback migration source."""
    sql_path = Path(SOURCE_TICKET_SQL_PATH)
    if not sql_path.exists():
        raise FileNotFoundError(f"Ticket seed SQL not found at {sql_path}")

    sql_text = sql_path.read_text(encoding="utf-8")
    match = re.search(
        r"INSERT INTO tickets\s*\n\(title, description, member_id, location_id, category_id, priority, status_id, created_at, updated_at\) VALUES\s*(.*?);",
        sql_text,
        re.DOTALL,
    )
    if not match:
        raise ValueError(f"Could not parse ticket seed rows from {sql_path}")

    tuples = literal_eval("[" + match.group(1).strip() + "]")
    rows = []
    for offset, values in enumerate(tuples, start=1):
        rows.append(
            {
                "ticket_id": offset,
                "title": values[0],
                "description": values[1],
                "member_id": values[2],
                "location_id": values[3],
                "category_id": values[4],
                "priority": values[5],
                "status_id": values[6],
                "created_at": values[7],
                "updated_at": values[8],
            }
        )
    return rows


def load_source_tickets():
    """Load monolithic ticket source rows for migration or verification."""
    rows = _load_tickets_from_db()
    if rows is not None:
        return rows, "legacy_db"
    return _load_tickets_from_sql_seed(), "track1_sql_seed"
