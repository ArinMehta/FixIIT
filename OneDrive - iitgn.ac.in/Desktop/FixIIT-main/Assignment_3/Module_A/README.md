# Module A: Transaction Engine & Crash Recovery

**Status:** ✅ COMPLETE

This module implements and validates ACID guarantees for your custom B+ Tree-based database system.

## What Module A Addresses

### Core Requirements Met

1. **B+ Tree as Storage Engine**
   - Single B+ tree per relation (members, tickets, assignments)
   - Primary key → B+ tree key
   - All operations directly modify B+ tree (no separate data copy)

2. **Transaction Support**
   - BEGIN: start transaction ← `custom_engine/engine.py:begin()`
   - COMMIT: apply all or none ← `custom_engine/engine.py:commit()`
   - ROLLBACK: discard changes ← `custom_engine/engine.py:rollback()`

3. **ACID Validation**
   - Atomicity: failure injection + rollback verification
   - Consistency: foreign key + referential integrity checks
   - Isolation: serialized commit lock prevents corruption
   - Durability: WAL logging + recovery on restart

4. **Multi-Relation Transactions**
   - Example: assign_ticket_transaction() touches 3 relations
   - Members (verify IDs exist)
   - Tickets (update status)
   - Assignments (insert new assignment)

5. **Failure & Recovery**
   - Crash during commit: injected via fail_after_ops parameter
   - Recovery: redo committed, undo incomplete transactions
   - Tested via database restart in run_acid_demo.py

## Files

| File | Purpose |
|------|---------|
| `custom_engine/engine.py` | Transaction engine, WAL, recovery logic (~400 lines) |
| `custom_engine/models.py` | FixIIT schema, validator, initialization (~120 lines) |
| `custom_engine/__init__.py` | Module exports |
| `run_acid_demo.py` | ACID demonstration script (~150 lines) |
| `run_isolation_demo.py` | Isolation-specific demonstration (dirty-read prevention) |
| `custom_engine_state/` | Persistent storage (auto-created) |

## Run Module A

```powershell
cd Assignment_3/Module_A
"C:\\Program Files\\Python313\\python.exe" run_acid_demo.py
```

```powershell
cd Assignment_3/Module_A
"C:\\Program Files\\Python313\\python.exe" run_isolation_demo.py
```

## What Output Shows

1. **Initial State**
   - Bootstrap data: 5 members, 3 tickets, 2 assignments

2. **Atomicity Test**
   - Crash injected after 2 operations (before 3rd)
   - State remains unchanged (no partial commit)
   - Verification: "[OK] Atomicity verified: partial transaction was rolled back"

3. **Consistency Test**
   - Successful multi-table commit
   - All foreign key references valid
   - Verification: "[OK] Consistency check passed: all foreign keys valid"

4. **Durability Test**
   - Database restarted (new process, same storage)
   - Committed state persists
   - Verification: "[OK] Durability verified: state matches after restart"

## Key Evidence for Report

### 1. Atomicity
- Screenshot JSON before/after failure
- Caption: "Transaction rolled back; no partial updates"

### 2. Consistency
- Screenshot final state with FK references
- Validator error message if violated
- Caption: "Constraints enforced before commit"

### 3. Isolation
- Run `run_isolation_demo.py`
- Show output line: "[OK] Isolation check #1 passed: no dirty read"
- Show output line: "[OK] Isolation check #2 passed: committed data is visible after commit"

### 4. Durability
- Screenshot initial commit state
- Screenshot after restart
- Caption: "Data persists across process restarts"

## Technical Details

### Storage Layout

```
Module_A/
├── custom_engine_state/
│   ├── wal.jsonl                 (write-ahead log, all transactions)
│   ├── metadata.json             (table schemas)
│   └── tables/
│       ├── members.json
│       ├── tickets.json
│       └── assignments.json
```

### Transaction Lifecycle

```
BEGIN
  ↓
stage operations (insert/update/delete)
  ↓
COMMIT
  ├─ validate state (run fixiit_validator)
  ├─ apply operations to B+ tree
  ├─ (optional: inject failure)
  ├─ write WAL COMMIT record
  ├─ persist tables to disk
  └─ mark success
  
or
  
ROLLBACK
  ├─ restore before-images from WAL
  ├─ write WAL ABORT record
  └─ discard staged operations
```

### Recovery Process

```
Restart Database
  ↓
Read WAL file
  ↓
Group transactions by ID
  ├─ COMMITTED: replay after-images (redo)
  └─ ABORTED: replay before-images (undo)
  ↓
Persist recovered state
```

## For Your Team

- **Run time:** ~5-10 seconds
- **Evidence needed:** Console output (JSON state before/after failure, durability check)
- **Report section:** Module A ACID explanations + screenshots
