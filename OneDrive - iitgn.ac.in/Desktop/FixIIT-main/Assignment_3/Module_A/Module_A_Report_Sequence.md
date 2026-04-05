# Module A: Clean Report & Video Sequence

**Deadline:** 6 PM, April 5, 2026

## Files You're Using

| File | Purpose | For Report |
|------|---------|----------|  
| `Assignment_3/Module_A/run_acid_demo.py` | Tests A, C, I, D (Atomicity, Consistency, Isolation, Durability) | ✓ Primary |
| `Assignment_3/Module_A/run_edge_cases.py` | Tests 6 edge cases mapping to assignment requirements | ✓ Optional (add if space) |
| `Assignment_3/Module_A/custom_engine/engine.py` | Engine code with locks, WAL, recovery | Code refs |
| `Assignment_3/Module_A/custom_engine/models.py` | FixIIT schema (members, tickets, assignments) | Code refs |
| `Assignment_3/Module_A/run_isolation_demo.py` | Legacy isolation-only backup | Optional backup |


## One-Time Setup (before first run)

```powershell
cd "c:\Users\shiva\OneDrive - iitgn.ac.in\Desktop\FixIIT-main\Assignment_3\Module_A"

# Clean state before running
Remove-Item -Path "custom_engine_state" -Recurse -Force -ErrorAction SilentlyContinue

# Run combined ACID file (A, C, I, D)
python .\run_acid_demo.py

# Run edge cases separately
python .\run_edge_cases.py
```

Results summary:
```
run_acid_demo.py   → [OK] All ACID checks completed
run_edge_cases.py  → [OK] All edge cases completed
```

---

## Edge Cases: Which to Include in Report?

**6 edge cases in `run_edge_cases.py`:**

| Edge Case | Maps to Requirement | Include? |
|-----------|-----|--|
| 1. Crash after 1st write | "Partial updates rolled back" | ✓ YES |
| 2. Crash after N writes | "Partial updates rolled back" | ✓ YES |
| 3. Duplicate key insert | "Ensure consistency" | ✓ YES |
| 4. Foreign key violation | "Ensure consistency" | ✓ YES |
| 5. Empty transaction rollback | "Idempotent recovery" | ○ OPTIONAL |
| 6. Committed data survives restarts | "Retain committed transactions" | ✓ YES |

**For Report:** Include edge cases 1, 2, 4, 6 (skip 3, 5 if report getting long) = 1-2 pages

**For Video:** Show 3 key edge cases [1, 4, 6] (+3 minutes)

---

## WAL Display: Report Screenshot vs Video?

**Option A: Report Screenshot (if report <5 pages)**
- Take screenshot of folder: `Assignment_3/Module_A/custom_engine_state/`
- Show `wal.jsonl` file exists + contains transaction records
- Caption: "Write-ahead log ensures durability"

**Option B: Video Walkthrough (more engaging, +1 min)**
- Open `wal.jsonl` in text editor
- Show 2-3 transaction records:
  - BEGIN record with tx_id
  - APPLY record with before/after images
  - COMMIT or ABORT record
- Say: "Every operation is logged before applied to B+ trees. On restart, recovery replays these records."

**Recommendation:** Use both - screenshot in report + walkthrough in video

---

## File Structure: Separate vs Combined?

**KEEP CURRENT STRUCTURE (Don't Combine):**
```
Assignment_3/Module_A/
├── custom_engine/ (engine code)
├── run_acid_demo.py
├── run_isolation_demo.py
├── run_edge_cases.py        ← NEW: failure scenarios
├── README.md
└── custom_engine_state/ (auto-created storage)
```

**Why separate?**
- ✓ Easy to run individually: `python .\.run_acid_demo.py`
- ✓ Easy to screenshot: run once, capture output
- ✓ Easy to debug: single failing test doesn't require reading 500-line file
- ✓ Clean for submission: shows organization

**For backup only:** Make `ALL_TESTS_COMBINED.py` (don't submit)

**In report, reference them:**
```
Appendix A: run_acid_demo.py (lines 1-150)
Appendix B: run_isolation_demo.py (full)
Appendix C: run_edge_cases.py (selected cases: 1, 2, 4, 6)
```

---

## Report Section 1: ACID Overview

Write this in your report:

**We demonstrate ACID properties on a B+ tree-based database using a multi-relation transaction that assigns tickets to technicians. The transaction touches 3 relations (members, tickets, assignments) and either succeeds completely or fails completely. In the same script, we also demonstrate isolation by showing that uncommitted changes are invisible to concurrent transactions. We cover not only standard ACID scenarios but also failure injection and recovery edge cases.**

## Screenshot Sequence (for PDF report)

### Screenshot 1: Initial Bootstrap State
Capture this output block from `run_acid_demo.py`:
```
=== Initial State (FixIIT Schema: members, tickets, assignments) ===
{ "members": [...5 members...], "tickets": [...3 tickets...], "assignments": [...] }
```

Caption:
```
Figure 1: FixIIT database bootstrap state. Three relations initialized:
- members: 5 records (Prof XYZ, Shiv Patel, Prof ABC, Electrician A, Admin)
- tickets: 3 records (Projector, Power outlet, AC issues)
- assignments: 2 records (existing assignments)
```

---

### Screenshot 2: Atomicity Test (Part A - Failure)
Capture:
```
=== Atomicity Test (Injected failure mid-commit) ===
Attempting to assign ticket 2 to technician 17 with admin 28...
[ATOMICITY] Expected failure captured: Injected failure after 2 operation(s)
```

Caption:
```
Figure 2a: Injected failure. Multi-table transaction attempts assignment 
but fails after 2 of 3 operations (before INSERT to assignments table).
```

---

### Screenshot 3: Atomicity Test (Part B - State After Failure)
Capture state JSON showing no new assignment was added:
```
=== ATOMICITY CHECK] State after failure:
{ "members": [...unchanged...], "tickets": [...unchanged...], 
  "assignments": [...no new record with id=100...] }
[OK] Atomicity verified: partial transaction was rolled back
```

Caption:
```
Figure 2b: State after injected failure. Database remains unchanged—no 
partial updates were persisted. The attempted INSERT (assignment_id=100) 
never occurred, proving atomicity (all-or-nothing principle).
```

---

### Screenshot 4: Consistency Test (Success)
Capture:
```
=== Consistency Test (Multi-relation validation) ===
Valid commit with ticket 3 assignment...
[OK] Consistency check passed: all foreign keys valid
```

Caption:
```
Figure 3: Successful multi-table commit. Ticket 3 (AC issue) is now 
assigned to Technician 17 by Admin 28. All foreign key constraints 
(ticket_id, technician_member_id, assigned_by) verified before commit.
```

---

### Screenshot 5: Durability/Recovery Test
Capture:
```
=== Durability/Recovery Test (Restart DB) ===
[OK] Durability verified: state matches after restart
[INFO] WAL location: C:\...\Assignment_3\Module_A\custom_engine_state\wal.jsonl
[OK] All ACID checks completed
```

Caption:
```
Figure 4: Durability verification. Database was restarted (new process, 
same storage). Committed transaction persists; uncommitted transaction 
from atomicity test remains rolled back. WAL file logs all operations 
for crash recovery.
```

---

### Screenshot 6: Isolation Test - T2 Cannot See T1 Uncommitted
Capture:
```
=== Isolation Test (No Dirty Reads) ===
[STEP] T1 staged update (uncommitted): priority=Isolation-T1
[STEP] T2 read before T1 commit: 
{
  "ticket_id": 1,
  "title": "Projector not working",
  "priority": "Medium",          <-- NOT "Isolation-T1"
  ...
}
[OK] Isolation check #1 passed: no dirty read
```

Caption:
```
Figure 5a: Isolation Level 1 - No Dirty Reads. Transaction T1 locally 
updates ticket 1 (priority → "Isolation-T1") but has not committed. 
Concurrent transaction T2 reads the same ticket and sees the original 
value ("Medium"), not T1's uncommitted update. Proves dirty-read prevention.
```

---

### Screenshot 7: Isolation Test - T3 Sees T1 After Commit
Capture:
```
[STEP] T3 read after T1 commit: 
{
  "ticket_id": 1,
  "title": "Projector not working",
  "priority": "Isolation-T1",      <-- NOW UPDATED
  ...
}
[OK] Isolation check #2 passed: committed data is visible after commit
[INFO] Commit critical section is serialized by an RLock in engine.commit().
```

Caption:
```
Figure 5b: Isolation Level 2 - Read Committed Data. After T1 commits 
its update, new transaction T3 reads ticket 1 and now sees the updated 
priority ("Isolation-T1"). Serialized RLock ensures no concurrent 
corruption during commit phase.
```

---

5. **(Optional) Show Edge Cases (1 min):**
   - Terminal: `python .\run_edge_cases.py`
   - Highlight: [PASS] lines for edge cases 1, 4, 6
   - Say: "These are advanced failure scenarios. All tests pass, proving robustness."

---

## Report Section 2: Implementation Explanation

### Atomicity
Write in report:
```
Atomicity is implemented via snapshot-before-and-restore mechanism. 
When a transaction enters the commit phase:
1. A snapshot of the entire database state is taken
2. All staged operations are simulated on a copy
3. Validators (e.g., FK checks) run on the simulated state
4. Only if validation passes, operations are applied to the real B+ trees
5. If any operation fails, the snapshot is restored using rollback logic

In our test, the transaction fails after 2 of 3 operations. The engine 
catches the exception, restores the before-snapshot, and writes an ABORT 
record to the WAL. Result: zero partial updates, zero corruption.
```

### Consistency
Write in report:
```
Before any commit, a validator function checks the proposed new state 
for referential integrity violations. In the FixIIT schema:
- Every ticket_id in assignments must exist in tickets
- Every technician_member_id in assignments must exist in members
- Every assigned_by in assignments must exist in members

The validator runs on the simulated state before B+ trees are modified. 
If any FK reference is broken, the commit is rejected and the transaction 
is rolled back. Test output "[OK] Consistency check passed" confirms 
all constraints were enforced.
```

### Isolation
Write in report:
```
Isolation is enforced via a threading.RLock(). The commit phase is the 
critical section:
1. Transaction T1 acquires the lock
2. All other transactions (T2, T3, etc.) wait for the lock
3. T1 applies changes to B+ trees and updates the WAL
4. T1 releases the lock
5. Waiting transactions proceed

This serialization prevents:
- Dirty reads (T2 cannot see T1's uncommitted updates)
- Lost updates (only one transaction modifies each B+ tree node at a time)
- Phantom reads (all committed data is stable before unlock)

Result: no data corruption under concurrent load. [See Module B for stress testing.]
```

### Durability
Write in report:
```
Durability is achieved via Write-Ahead Logging (WAL) and os.fsync():
1. Before applying any operation to B+ trees, a record is written to wal.jsonl
2. os.fsync() forces the record to disk, not just to kernel buffer
3. Transaction records include: BEGIN, APPLY (before/after images), COMMIT, ABORT
4. On database restart, the recover() function reads the WAL file
5. For each transaction:
   - If COMMIT found: replay after-images (redo all operations)
   - If ABORT or incomplete: replay before-images in reverse (undo all operations)

Result: committed data persists; uncommitted data is discarded. 
[See WAL file: Assignment_3/Module_A/custom_engine_state/wal.jsonl]
```

---

## Failure Handling & Recovery (Optional: Advanced Coverage)

If you want to highlight failure scenarios specifically (as per assignment requirement):

**For Report:**
```
Section: "Failure Injection & Recovery"

We simulate three categories of failures:

1. Crash after first write (Edge Case 1)
   - Injected at: first B+ tree operation
   - Expected: all writes rolled back, atomicity verified
   - Observed: [PASS] Partial write was rolled back

2. Crash after multiple writes (Edge Case 2)
   - Injected at: after 2 of 3 operations
   - Expected: all writes rolled back despite multi-table scope
   - Observed: [PASS] All writes rolled back

3. Constraint violations (Edge Cases 3, 4)
   - Duplicate key: rejected at insert time
   - Foreign key: caught during pre-commit validation
   - Expected: transaction aborted, no partial state
   - Observed: [PASS] Violations detected before commit

4. Recovery after restart (Edge Case 6)
   - Committed transactions: replayed from WAL (after-images)
   - Incomplete transactions: undone from WAL (before-images)
   - Expected: idempotent recovery, same state after multiple restarts
   - Observed: [PASS] Recovery is idempotent across restarts
```

**For Video:**
- Show 1-2 edge case failures in terminal output
- Explain: "Even with failures, no corruption. WAL ensures recovery."
- This demonstrates assignment requirement: "Ensure partial updates are rolled back, committed data is preserved"

---

## Video Sequence (5-7 minutes, Module A only)

1. **Intro (30 sec):** Show file structure
   - Point to: run_acid_demo.py, run_isolation_demo.py, custom_engine/engine.py, models.py
   - Say: "Module A tests ACID properties of a custom B+ tree transaction engine"

2. **Run ACID Demo (1 min):** 
   - Terminal: `python .\run_acid_demo.py`
   - Pause and read each section:
     - Initial state: "5 members, 3 tickets, 2 assignments"
     - Atomicity: "Injected failure after 2 ops, all rolled back"
     - Consistency: "New assignment created with valid FK references"
     - Durability: "After restart, committed state persists"

3. **Show WAL File (1 min):**
   - Open folder: `Assignment_3/Module_A/custom_engine_state/`
   - Show file: `wal.jsonl`
   - Open in text editor, scroll through showing:
     - BEGIN records (tx-xxxxx)
     - APPLY records with before/after images
     - COMMIT and ABORT records
   - Say: "This is the write-ahead log. Every operation is recorded before being applied to B+ trees."

4. **Run Isolation Demo (1 min):**
   - Terminal: `python .\run_isolation_demo.py`
   - Highlight:
     - "T2 read before T1 commit" → priority = "Medium" (not the updated value)
     - "[OK] Isolation check #1 passed: no dirty read"
     - "T3 read after T1 commit" → priority = "Isolation-T1" (updated value visible)
     - "[OK] Isolation check #2 passed: committed data is visible after commit"
   - Say: "Isolation prevents dirty reads. Uncommitted changes are invisible to other transactions."

5. **Code Overview (1 min):**
   - Show engine.py:
     - Line 84: `self._lock = threading.RLock()` — this serializes commits
     - Lines 128-161: commit() function with failure injection and rollback
     - Line 187: recover() function for crash recovery
     - Line 392: _write_wal() with os.fsync()
   - Say: "All four ACID properties are implemented: atomicity via snapshots, consistency via validator, isolation via lock, durability via WAL."

6. **Summary Slide (30 sec):**
   - Write on screen or say:
     ```
     Module A Validation Results:
     ✓ Atomicity: Rolled back partial transactions
     ✓ Consistency: Foreign keys enforced before commit
     ✓ Isolation: No dirty reads, serialized locking
     ✓ Durability: Committed data survives restart
     
     All tests passed. Ready for Module B: Concurrent stress testing.
     ```

---

## Run Sequence for Clean Report & Video

### Clean State & Run All Tests:
```powershell
cd "Assignment_3/Module_A"
Remove-Item -Path "custom_engine_state" -Recurse -Force -ErrorAction SilentlyContinue
python .\.run_acid_demo.py          # 1-2 minutes (A, C, D output)
python .\.run_isolation_demo.py     # 30 seconds (I output)
python .\.run_edge_cases.py         # 1 minute (edge case outputs)
```

### For Report Screenshots (in order):
1. Initial state JSON (5 members, 3 tickets)
2. Atomicity failure line + state JSON (no new assignment)
3. Consistency OK line
4. Durability OK line + WAL path
5. Isolation demo: T2 read (old value) + T3 read (new value)
6. (Optional 1 page) Edge cases 1, 2, 4, 6 summary blocks
7. WAL file screenshot

### For Video (4-7 minutes):
1. Show Module_A folder structure (10 sec)
2. Run `run_acid_demo.py` (2 min) - pause at each [OK]
3. Open & show WAL file in text editor (1 min)
4. Run `run_isolation_demo.py` (1 min)
5. (Optional) Run `run_edge_cases.py` (1 min) - show 3 key outputs
6. Code walkthrough: engine.py lines for locks, WAL, recovery (1 min)

---

## What Proves Full Marks for Module A

1. ✅ B+ tree storage engine (Assignment_2/Module_A referenced, not copied)
2. ✅ 3-relation transaction (members, tickets, assignments)
3. ✅ BEGIN/COMMIT/ROLLBACK API (run_acid_demo.py uses all three)
4. ✅ Atomicity proof (failure injection, rollback verification)
5. ✅ Consistency proof (FK validator enforced before commit)
6. ✅ Isolation proof (dirty-read prevention, serialized locks)
7. ✅ Durability proof (WAL logging, recovery on restart)
8. ✅ Failure injection + recovery (explicit testing in both scripts)
9. ✅ Multi-table operations (3 tables touched in single transaction)
10. ✅ WAL file visible and correctly formatted

All 10 items are demonstrated in Module A. Video + report covers all.

---

## Report Writing Order

1. Objective: ACID validation on custom B+ tree
2. Schema: 3 relations + their roles
3. Transaction model: BEGIN/COMMIT/ROLLBACK
4. Implementation: WAL, recovery, snapshot, locks
5. ACID tests: 4 subsections (A, C, I, D) with screenshots
6. Observations: What works, what doesn't, why
7. Conclusion: All properties validated, ready for Module B

**Estimated report section length:** 3-4 pages (with figures)
