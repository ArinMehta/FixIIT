from __future__ import annotations

from pathlib import Path
from typing import Dict

from .engine import TransactionalBPlusDatabase


FIXIIT_SCHEMAS = {
    "members": {
        "member_id": "int",
        "name": "str",
        "email": "str",
        "contact_number": "str",
        "age": "int",
    },
    "tickets": {
        "ticket_id": "int",
        "title": "str",
        "member_id": "int",
        "category_id": "int",
        "priority": "str",
        "status_id": "int",
    },
    "assignments": {
        "assignment_id": "int",
        "ticket_id": "int",
        "technician_member_id": "int",
        "assigned_by": "int",
        "instructions": "str",
    },
}


def fixiit_validator(state: Dict[str, Dict[object, dict]]) -> None:
    members = state.get("members", {})
    tickets = state.get("tickets", {})
    assignments = state.get("assignments", {})

    # Validate referential integrity
    for ticket in tickets.values():
        if ticket["member_id"] not in members:
            raise ValueError(
                f"Consistency violation: tickets.member_id {ticket['member_id']} "
                f"does not reference valid member"
            )

    for assignment in assignments.values():
        ticket_id = assignment["ticket_id"]
        if ticket_id not in tickets:
            raise ValueError(
                f"Consistency violation: assignments.ticket_id {ticket_id} "
                f"does not reference valid ticket"
            )
        tech_id = assignment["technician_member_id"]
        if tech_id not in members:
            raise ValueError(
                f"Consistency violation: assignments.technician_member_id {tech_id} "
                f"does not reference valid member"
            )
        assigned_by = assignment["assigned_by"]
        if assigned_by not in members:
            raise ValueError(
                f"Consistency violation: assignments.assigned_by {assigned_by} "
                f"does not reference valid member"
            )


def init_fixiit_db(storage_dir: str) -> TransactionalBPlusDatabase:
    db = TransactionalBPlusDatabase(storage_dir=storage_dir, order=8)

    for table_name, schema in FIXIIT_SCHEMAS.items():
        if table_name not in db.tables:
            key = next(iter(schema))
            db.create_table(table_name, schema=schema, search_key=key)

    db.register_validator(fixiit_validator)

    if not db.get_all("members"):
        tx = db.begin()
        
        # Bootstrap sample member data from FixIIT schema
        tx.insert("members", {"member_id": 1, "name": "Prof. XYZ", "email": "prof.xyz@iitgn.ac.in", "contact_number": "+91 9123456789", "age": 37})
        tx.insert("members", {"member_id": 2, "name": "Shiv Patel", "email": "shiv.patel@iitgn.ac.in", "contact_number": "+91 8123406789", "age": 20})
        tx.insert("members", {"member_id": 3, "name": "Prof. ABC", "email": "prof.abc@iitgn.ac.in", "contact_number": "+91 7123456190", "age": 42})
        tx.insert("members", {"member_id": 17, "name": "Electrician A", "email": "electrician.a@fixiit.iitgn.ac.in", "contact_number": "+91 9000000001", "age": 32})
        tx.insert("members", {"member_id": 28, "name": "Admin", "email": "admin@fixiit.iitgn.ac.in", "contact_number": "+91 9999999999", "age": 50})
        
        # Bootstrap sample tickets
        tx.insert("tickets", {"ticket_id": 1, "title": "Projector not working", "member_id": 1, "category_id": 1, "priority": "Medium", "status_id": 5})
        tx.insert("tickets", {"ticket_id": 2, "title": "Power outlet sparks", "member_id": 2, "category_id": 1, "priority": "Emergency", "status_id": 2})
        tx.insert("tickets", {"ticket_id": 3, "title": "AC not working in Lab", "member_id": 3, "category_id": 3, "priority": "High", "status_id": 2})
        
        # Bootstrap sample assignments
        tx.insert("assignments", {"assignment_id": 1, "ticket_id": 2, "technician_member_id": 17, "assigned_by": 28, "instructions": "Inspect wiring and replace damaged outlet."})
        tx.insert("assignments", {"assignment_id": 2, "ticket_id": 3, "technician_member_id": 17, "assigned_by": 28, "instructions": "Check AC unit cooling system."})
        
        tx.commit()

    return db


def storage_path_from_repo() -> str:
    root = Path(__file__).resolve().parents[2]
    return str(root / "Assignment_3" / "custom_engine_state")
