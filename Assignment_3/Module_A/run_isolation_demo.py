from __future__ import annotations

import json
from pathlib import Path

from custom_engine.models import init_fixiit_db, storage_path_from_repo


def main() -> None:
    storage = storage_path_from_repo()
    db = init_fixiit_db(storage)

    print("=== Isolation Demo (Module A) ===")

    # Start T1 and stage an update but do not commit yet.
    t1 = db.begin()
    ticket_before = t1.get("tickets", 1)
    if ticket_before is None:
        raise RuntimeError("Ticket 1 not found")

    staged = dict(ticket_before)
    staged["priority"] = "Isolation-T1"
    t1.update("tickets", 1, staged)

    # Start T2 while T1 is still open. T2 must not see T1's uncommitted write.
    t2 = db.begin()
    t2_view = t2.get("tickets", 1)

    print("[STEP] T1 staged update (uncommitted): priority=Isolation-T1")
    print(f"[STEP] T2 read before T1 commit: {json.dumps(t2_view, indent=2)}")

    if t2_view is not None and t2_view.get("priority") == "Isolation-T1":
        print("[FAIL] Isolation violated: T2 observed uncommitted write from T1")
    else:
        print("[OK] Isolation check #1 passed: no dirty read")

    # Commit T1. New transactions should now observe the committed value.
    t1.commit()
    t2.rollback()

    t3 = db.begin()
    t3_view = t3.get("tickets", 1)
    t3.rollback()

    print(f"[STEP] T3 read after T1 commit: {json.dumps(t3_view, indent=2)}")

    if t3_view is not None and t3_view.get("priority") == "Isolation-T1":
        print("[OK] Isolation check #2 passed: committed data is visible after commit")
    else:
        print("[FAIL] Isolation violated: committed data not visible as expected")

    print("\n[INFO] Commit critical section is serialized by an RLock in engine.commit().")
    print(f"[INFO] WAL location: {Path(storage) / 'wal.jsonl'}")


if __name__ == "__main__":
    main()
