"""Set up coordinator and shard databases for Assignment 4 sharding."""

from pathlib import Path
import sys


MODULE_B_DIR = Path(__file__).resolve().parents[1]
if str(MODULE_B_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_B_DIR))

from app.database import DatabaseError, ensure_database_exists, execute_sql_script
from app.sharding import all_ticket_shards
from config import COORDINATOR_DB_CONFIG


SQL_DIR = MODULE_B_DIR / "sql"


def _seed_coordinator_data():
    """Apply idempotent coordinator seed data so setup remains rerunnable."""
    execute_sql_script(SQL_DIR / "insert_sample_data.sql", COORDINATOR_DB_CONFIG)
    print("Coordinator sample data upserted idempotently.")


def main():
    """Create coordinator and shard schemas using the checked-in SQL files."""
    try:
        ensure_database_exists(COORDINATOR_DB_CONFIG)
        execute_sql_script(SQL_DIR / "create_tables.sql", COORDINATOR_DB_CONFIG)
        _seed_coordinator_data()

        # Try to create coordinator triggers, but skip if SUPER privilege is missing (remote servers)
        try:
            execute_sql_script(SQL_DIR / "create_audit_triggers.sql", COORDINATOR_DB_CONFIG)
            print("✅ Coordinator audit triggers created")
        except DatabaseError as trigger_exc:
            if "SUPER privilege" in str(trigger_exc) or "binary logging" in str(trigger_exc):
                print("⚠️  Coordinator triggers skipped (remote server limitation - SUPER privilege required)")
            else:
                raise

        print(
            "Coordinator ready:",
            COORDINATOR_DB_CONFIG["database"],
            f"on port {COORDINATOR_DB_CONFIG['port']}",
        )

        for shard_idx, shard_config in all_ticket_shards():
            ensure_database_exists(shard_config)
            execute_sql_script(SQL_DIR / "create_ticket_shard_tables.sql", shard_config)

            # Try to create shard triggers, but skip if SUPER privilege is missing
            try:
                execute_sql_script(
                    SQL_DIR / "create_ticket_shard_audit_triggers.sql",
                    shard_config,
                )
                print(f"✅ Shard {shard_idx} triggers created")
            except DatabaseError as trigger_exc:
                if "SUPER privilege" in str(trigger_exc) or "binary logging" in str(trigger_exc):
                    print(f"⚠️  Shard {shard_idx} triggers skipped (remote server limitation)")
                else:
                    raise

            print(
                f"Shard {shard_idx} ready:",
                shard_config["database"],
                f"on port {shard_config['port']}",
            )

        print("✅ Sharded database setup completed successfully.")
    except DatabaseError as exc:
        raise SystemExit(f"Setup failed: {exc}") from exc


if __name__ == "__main__":
    main()
