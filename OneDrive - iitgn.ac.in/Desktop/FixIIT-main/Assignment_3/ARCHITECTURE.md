# Architecture & Data Flow

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Assignment 3: FixIIT ACID System                     │
└─────────────────────────────────────────────────────────────────────────┘

                          ┌──────────────┐
                          │  User Code   │
                          │   (Script)   │
                          └──────┬───────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
          ┌─────────▼────┐  ┌──────▼────┐  ┌───▼──────────────┐
          │ ACID Demo    │  │  Stress   │  │ Backend Compare  │
          │(run_module_a)│  │ (stress_) │  │ (stress_compare) │
          | _acid_demo   │  │  compare) │  │                  │
          └──────┬───────┘  └──────┬────┘  └───┬──────────────┘
                 │                 │           │  
                 └─────────┬───────┴───────────┘
                           │
                 ┌─────────▼──────────┐
                 │ TransactionalDB    │
                 │ (engine.py)        │
                 └────────┬───────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼─────┐  ┌────────▼──────┐  ┌──────▼─────┐
   │ Members  │  │   Tickets     │  │ Assignments│
   │ (B+Tree) │  │   (B+Tree)    │  │ (B+Tree)   │
   └────┬─────┘  └────────┬──────┘  └──────┬─────┘
        │                 │                │
        └─────────────────┼────────────────┘
                          │ all backed by
                          │
                ┌─────────▼──────────┐
                │  custom_engine_    │
                │  state/            │
                │  ├─ wal.jsonl      │
                │  ├─ metadata.json  │
                │  └─ tables/*.json  │
                └────────────────────┘
```

## Transaction Lifecycle

```
BEGIN
  │
  ├─→ [staged_ops = []]
  │
  ├─→ insert/update/delete calls
  │   └─→ append Operation to staged_ops
  │
  ├─→ COMMIT
  │
  ├─→ Validation Phase
  │   ├─ ForEach operation:
  │   │  └─ snapshot before & simulate after
  │   └─ Call validator(simulated_state)
  │      └─ Check: all member_ids exist
  │      └─ Check: all ticket_ids exist
  │      └─ Check: all assignment refs valid
  │
  ├─→ Apply Phase (REAL WRITES)
  │   ├─ WriteWAL("APPLY", table, key, before, after)
  │   ├─ Apply operation to B+Tree
  │   ├─ [If fail_after_ops reached → Exception]
  │   └─ Repeat for each staged op
  │
  ├─→ Success
  │   ├─ WriteWAL("COMMIT", tx_id, op_count)
  │   ├─ Persist all tables to disk
  │   └─ Clear staged_ops
  │
  └─→ Failure (Exception at any point)
      ├─ RestoreSnapshot(before)
      ├─ WriteWAL("ABORT", reason)
      ├─ Persist rollback state
      └─ Clear staged_ops
```

## Recovery Process (On Restart)

```
ReadWAL()
  ├─→ Group by tx_id
  │
  ├─→ For each tx_id:
  │   ├─ COMMITTED transactions
  │   │  └─→ Apply all APPLY records (after-images)
  │   └─ ABORTED transactions
  │      ├─→ Read all APPLY records in reverse
  │      └─→ Apply before-images (undo)
  │
  └─→ Persist recovered tables to disk
```

## Schema & Constraints

```
┌─────────────────────────────────┐
│         members                 │
├─────────────────────────────────┤
│ member_id (PK) ────────────┐   │
│ name                       │    │
│ email                      │    │
│ contact_number             │    │
│ age                        │    │
└─────────────────────────────────┘
         ▲                    
         │ (referential integrity)
         │
┌────────┴────────────────────────┐          ┌──────────────────────────┐
│         tickets                 │◄─────────┤   assignments            │
├─────────────────────────────────┤          ├──────────────────────────┤
│ ticket_id (PK)                  │          │ assignment_id (PK)       │
│ title                           │          │ ticket_id (FK)           │
│ member_id (FK)──────────┐       │          │ technician_member_id(FK) │
│ category_id │           │       │          │ assigned_by (FK)         │
│ priority    │           ├─→────┼──►────┐  │ instructions             │
│ status_id   │           │       │       │  └──────────────────────────┘
└─────────────┼───────────┘       │       │
              │ (FK constraints    │       │
              │  enforced before   │       │
              └─ commit)          │       │
                                  │       │
                                  ├─►─────┤
                                  │       │
                           (both point to members)
```

## ACID Properties Mapped to Code

| Property | Mechanism | Code Location |
|----------|-----------|---|
| **Atomicity** | All-or-nothing commit; exception → rollback | `engine.py:apply_phase()`, `restore_snapshot()` |
| **Consistency** | Validator run before commit; FK checks | `models.py:fixiit_validator()` |
| **Isolation** | Serialized `_lock` during commit | `engine.py:_lock = RLock()` |
| **Durability** | WAL flush + fsync + persistent snapshots | `engine.py:_write_wal()`, `_persist_all_tables()` |

## Test Coverage

### Module A: Atomicity
```python
purchase_transaction(fail_after_ops=2)  # Crashes after 2 of 3 operations
# Expected: No partial state, all rolled back
# Verified: JSON output shows unchanged state
```

### Module A: Consistency
```python
fixiit_validator(state) raises ValueError if:
  - ticket.member_id not in members
  - assignment.ticket_id not in tickets
  - assignment.technician/assigned_by not in members
```

### Module A: Durability
```python
db1 = init_fixiit_db(storage)
commit_transaction()
save_state = pretty_state(db1)

db2 = init_fixiit_db(storage)  # Restart
final_state = pretty_state(db2)

assert save_state == final_state  # ✓ Durable
```

### Module B: Isolation + Concurrent Behavior
```python
ThreadPoolExecutor(workers=16) submits 200+ concurrent transactions
# Expected:
#  - 185+ commits (success)
#  - 15 rollbacks (injected failures)
#  - No corruption, no lost updates
# Metrics: throughput RPS, latency p95
```

## File Manifest

```
Assignment_3/
│
├── custom_engine/
│   ├── __init__.py ......................... Exports (TransactionalBPlusDatabase, init_fixiit_db, etc.)
│   ├── engine.py ........................... Core transaction engine (700 lines)
│   └── models.py ........................... FixIIT schema + validator (80 lines)
│
├── custom_engine_state/ .................... (auto-created by first run)
│   ├── wal.jsonl ........................... Write-ahead log (all transactions)
│   ├── metadata.json ....................... Table schemas
│   └── tables/
│       ├── members.json
│       ├── tickets.json
│       └── assignments.json
│
├── run_module_a_acid_demo.py .............. ACID verification script (70 lines)
├── stress_compare.py ....................... Concurrent workload + comparison (180 lines)
│
├── results/
│   └── backend_comparison.csv ............. Stress test results (custom + SQL)
│
├── README.md .............................. Quick start guide
├── REPORT_GUIDE.md ........................ Detailed report structure + evidence
├── STATUS.md ............................. This status summary
├── requirements.txt ....................... Python dependencies
└── ARCHITECTURE.md ........................ This file

Total: ~1000 lines of custom code + full ACID implementation
```

---

## Performance Characteristics

### Custom B+ Tree Engine (Observed)
- **Throughput:** ~15-20 req/s (multi-threaded, 16 workers)
- **Latency:** 997ms avg, 1463ms p95 (high due to serialized commit lock)
- **Commits:** 92.5% success rate (185/200 with 10% injected failure ratio)
- **Scalability:** Single-threaded recovery; suitable for study project

### Expected SQL Backend (when DB available)
- **Throughput:** ~10-12 req/s (MySQL connection overhead)
- **Latency:** ~1600-2000ms (network + query parsing)
- **Commits:** ~100% (unless schema/config issues)

**Observation:** Custom slower (expected), but demonstrates correct ACID semantics.

---

## Next Developer Notes

If extending this:

1. **Multi-txn interleaving:** Remove `_lock` for true MVCC (complex)
2. **Distributed ACID:** Add 2-phase commit protocol
3. **Indexing:** Adapt WAL/recovery for secondary indexes
4. **Persistence:** Switch from JSON to binary format (faster)
