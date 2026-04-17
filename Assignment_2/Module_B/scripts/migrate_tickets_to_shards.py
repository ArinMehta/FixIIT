"""Migrate monolithic tickets into the 3-shard Assignment 4 layout."""

from collections import Counter
from pathlib import Path
import sys


MODULE_B_DIR = Path(__file__).resolve().parents[1]
if str(MODULE_B_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_B_DIR))

from app.database import (
    DatabaseError,
    advance_ticket_id_allocator,
    execute_write,
    fetch_one,
    mark_ticket_sharding_migration_complete,
)
from app.sharding import all_ticket_shards, get_ticket_shard_config, shard_for_member
from app.ticket_source import load_source_tickets


MIGRATION_AUDIT_CONTEXT = {
    "actor_member_id": 0,
    "endpoint": "scripts/migrate_tickets_to_shards.py",
}


def _existing_ticket_shards(ticket_id):
    """Return all shards that already contain the given ticket_id."""
    hits = []
    for shard_idx, shard_config in all_ticket_shards():
        row = fetch_one(
            "SELECT ticket_id FROM tickets WHERE ticket_id = %s",
            (ticket_id,),
            db_config=shard_config,
        )
        if row:
            hits.append(shard_idx)
    return hits


def _existing_ticket_locator(ticket_id):
    """Return the existing locator row for ticket_id, if present."""
    return fetch_one(
        """
        SELECT ticket_id, member_id, shard_idx
        FROM ticket_locator
        WHERE ticket_id = %s
        """,
        (ticket_id,),
    )


def _sync_global_ticket_id_allocator(source_rows):
    """Advance the coordinator ticket_id allocator past all migrated ticket_ids."""
    max_source_ticket_id = max(int(row["ticket_id"]) for row in source_rows) if source_rows else 0
    next_ticket_id = advance_ticket_id_allocator(max_source_ticket_id + 1)
    print(f"Coordinator ticket_id allocator advanced to next_ticket_id={next_ticket_id}")


def _collect_conflicts(source_rows):
    """Detect any pre-existing ticket_id collisions before performing writes."""
    conflicts = []
    for row in source_rows:
        ticket_id = int(row["ticket_id"])
        member_id = int(row["member_id"])
        shard_idx = shard_for_member(member_id)
        existing_shards = _existing_ticket_shards(ticket_id)
        existing_locator = _existing_ticket_locator(ticket_id)

        if existing_shards or existing_locator:
            conflicts.append(
                {
                    "ticket_id": ticket_id,
                    "target_shard": shard_idx,
                    "existing_shards": existing_shards,
                    "existing_locator_shard": (
                        int(existing_locator["shard_idx"]) if existing_locator else None
                    ),
                }
            )

    return conflicts


def main():
    """Copy source tickets into the canonical 3-shard ticket layout."""
    try:
        source_rows, source_name = load_source_tickets()
        if not source_rows:
            raise SystemExit("No source tickets found for migration.")

        conflicts = _collect_conflicts(source_rows)
        if conflicts:
            for conflict in conflicts:
                print(
                    "Conflict detected:",
                    f"ticket_id={conflict['ticket_id']}",
                    f"target_shard={conflict['target_shard']}",
                    f"existing_shards={conflict['existing_shards']}",
                    f"existing_locator_shard={conflict['existing_locator_shard']}",
                )
            raise SystemExit(
                "Migration aborted because pre-existing ticket_id collisions were found in the target state."
            )

        shard_counts = Counter()

        for row in source_rows:
            ticket_id = int(row["ticket_id"])
            member_id = int(row["member_id"])
            shard_idx = shard_for_member(member_id)
            target_shard_config = get_ticket_shard_config(shard_idx)

            execute_write(
                """
                INSERT INTO tickets (
                    ticket_id, title, description, member_id, location_id, category_id,
                    priority, status_id, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    ticket_id,
                    row["title"],
                    row["description"],
                    member_id,
                    row["location_id"],
                    row["category_id"],
                    row["priority"],
                    row["status_id"],
                    row["created_at"],
                    row["updated_at"],
                ),
                audit_context=MIGRATION_AUDIT_CONTEXT,
                db_config=target_shard_config,
            )
            execute_write(
                """
                INSERT INTO ticket_locator (
                    ticket_id, member_id, shard_idx, created_at, updated_at
                )
                VALUES (%s, %s, %s, NOW(), NOW())
                """,
                (ticket_id, member_id, shard_idx),
                audit_context=MIGRATION_AUDIT_CONTEXT,
            )
            shard_counts[shard_idx] += 1

        _sync_global_ticket_id_allocator(source_rows)
        mark_ticket_sharding_migration_complete()

        print(
            f"Migrated {len(source_rows)} source tickets from {source_name} into shards."
        )
        for shard_idx in sorted(shard_counts):
            print(f"Shard {shard_idx}: {shard_counts[shard_idx]} tickets")
    except DatabaseError as exc:
        raise SystemExit(f"Migration failed: {exc}") from exc


if __name__ == "__main__":
    main()
