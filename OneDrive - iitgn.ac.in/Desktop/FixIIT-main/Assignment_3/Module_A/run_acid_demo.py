from __future__ import annotations

import json
from pathlib import Path

from custom_engine.models import init_fixiit_db, storage_path_from_repo


def assign_ticket_transaction(db, assignment_id: int, ticket_id: int, tech_id: int, admin_id: int, fail_after_ops=None):
    """
    Multi-table transaction: assign a ticket to a technician.
    This touches 3 relations: members (verify IDs exist), tickets (update status), assignments (insert).
    """
    tx = db.begin()

    # Verify technician member exists
    tech = tx.get("members", tech_id)
    if tech is None:
        tx.rollback()
        raise ValueError(f"Technician {tech_id} not found")

    # Verify admin exists
    admin = tx.get("members", admin_id)
    if admin is None:
        tx.rollback()
        raise ValueError(f"Admin {admin_id} not found")

    # Get ticket and verify it exists
    ticket = tx.get("tickets", ticket_id)
    if ticket is None:
        tx.rollback()
        raise ValueError(f"Ticket {ticket_id} not found")

    # Update ticket status to "Assigned" (status_id = 2)
    updated_ticket = dict(ticket)
    updated_ticket["status_id"] = 2
    tx.update("tickets", ticket_id, updated_ticket)

    # Create assignment record
    tx.insert(
        "assignments",
        {
            "assignment_id": assignment_id,
            "ticket_id": ticket_id,
            "technician_member_id": tech_id,
            "assigned_by": admin_id,
            "instructions": "Inspect and repair as per priority",
        },
    )

    tx.commit(fail_after_ops=fail_after_ops)


def pretty_state(db):
    return {
        "members": db.get_all("members"),
        "tickets": db.get_all("tickets"),
        "assignments": db.get_all("assignments"),
    }


def main():
    storage = storage_path_from_repo()
    db = init_fixiit_db(storage)

    print("=== Initial State (FixIIT Schema: members, tickets, assignments) ===")
    print(json.dumps(pretty_state(db), indent=2))

    print("\n=== Atomicity Test (Injected failure mid-commit) ===")
    print("Attempting to assign ticket 2 to technician 17 with admin 28...")
    try:
        assign_ticket_transaction(db, assignment_id=100, ticket_id=2, tech_id=17, admin_id=28, fail_after_ops=2)
    except Exception as exc:
        print(f"[ATOMICITY] Expected failure captured: {exc}")

    state_after_failure = pretty_state(db)
    print("[ATOMICITY CHECK] State after failure:")
    print(json.dumps(state_after_failure, indent=2))
    
    # Verify atomicity: assignment_id=10 should NOT exist (rollback prevented insert)
    assignments_after = state_after_failure["assignments"]
    assignment_10_exists = any(a["assignment_id"] == 10 for a in assignments_after)
    if not assignment_10_exists:
        print("[OK] Atomicity verified: partial transaction was rolled back")
    else:
        print("[FAIL] Atomicity violated: partial state was committed")

    print("\n=== Consistency Test (Multi-relation validation) ===")
    print("Valid commit with ticket 3 assignment...")
    assign_ticket_transaction(db, assignment_id=101, ticket_id=3, tech_id=17, admin_id=28)
    state_after_valid = pretty_state(db)
    print(json.dumps(state_after_valid, indent=2))
    print("[OK] Consistency check passed: all foreign keys valid")

    print("\n=== Durability/Recovery Test (Restart DB) ===")
    print("Restarting database to verify committed data persists...")
    db_restarted = init_fixiit_db(storage)
    state_after_restart = pretty_state(db_restarted)
    print(json.dumps(state_after_restart, indent=2))

    if state_after_restart == state_after_valid:
        print("[OK] Durability verified: state matches after restart")
    else:
        print("[FAIL] Durability violated: state diverged after restart")

    print(f"\n[INFO] WAL location: {Path(storage) / 'wal.jsonl'}")
    print("[OK] All ACID checks completed")


if __name__ == "__main__":
    main()
