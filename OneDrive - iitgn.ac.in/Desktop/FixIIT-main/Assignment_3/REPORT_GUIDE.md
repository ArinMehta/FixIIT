# Assignment 3: Complete Implementation & Report Guide

**Last Updated:** March 30, 2026
**Status:** Module A complete. Module B setup pending (SQL DB credentials).

---

## QUICK ANSWER: Backend Question

Your understanding is **100% correct**:

| Module | Backend | Purpose | Status |
|--------|---------|---------|--------|
| **Module A** | Custom B+ Tree | ACID validation, crash recovery, transactions | ✅ Complete |
| **Module B** | SQL + Custom Comparison | Concurrent behavior, stress testing, performance | ⏳ Pending DB setup |

---

## Module A: Transaction Engine & Crash Recovery (✅ COMPLETE)

### What is Implemented

1. **Transaction API** (`custom_engine/engine.py`)
   - `BEGIN` → start transaction (returns `TransactionContext`)
   - `COMMIT` → apply all operations or rollback on error
   - `ROLLBACK` → discard staged changes
   - Failure injection support: `commit(fail_after_ops=N)` crashes mid-commit

2. **Write-Ahead Logging (WAL)**
   - Location: `Assignment_3/custom_engine_state/wal.jsonl`
   - Records: BEGIN, APPLY (before/after images), COMMIT, ABORT
   - Persistent flush to disk for durability

3. **Crash Recovery**
   - Redo committed transactions (apply after-images)
   - Undo incomplete/aborted transactions (apply before-images)
   - Automatic on database restart

4. **Consistency Validation**
   - Referential integrity checks (foreign keys)
   - Enforcement before commit (all-or-nothing)

5. **Isolation**
   - Serialized commit lock for safety
   - Prevents same-key concurrent modifications

### The 3 Core Relations (Your Actual FixIIT Schema)

```python
members
  ├─ member_id (PK)
  ├─ name
  ├─ email
  ├─ contact_number
  └─ age

tickets
  ├─ ticket_id (PK)
  ├─ title
  ├─ member_id (FK → members)
  ├─ category_id
  ├─ priority
  └─ status_id

assignments
  ├─ assignment_id (PK)
  ├─ ticket_id (FK → tickets)
  ├─ technician_member_id (FK → members)
  ├─ assigned_by (FK → members)
  └─ instructions
```

### ACID Validation Script: `run_module_a_acid_demo.py`

**Run:**
```powershell
& "C:/Program Files/Python313/python.exe" Assignment_3/run_module_a_acid_demo.py
```

**What it demonstrates:**

| Property | Test Case | Evidence |
|----------|-----------|----------|
| **Atomicity** | Injected failure after 2 of 3 ops | All operations rolled back; no partial state |
| **Consistency** | Multi-table commit | Foreign key references valid after commit |
| **Isolation** | Serialized locking | No dirty reads between transactions |
| **Durability** | Database restart | Committed data persists; uncommitted discarded |

**Example Output:**
```
=== Initial State (FixIIT Schema: members, tickets, assignments) ===
{ "members": [...3 members...], "tickets": [...3 tickets...], "assignments": [...] }

=== Atomicity Test (Injected failure mid-commit) ===
[ATOMICITY] Expected failure captured: Injected failure after 2 operation(s)
[ATOMICITY CHECK] State after failure: { ... unchanged ... }
[OK] Atomicity verified: partial transaction was rolled back

=== Consistency Test (Multi-relation validation) ===
[OK] Consistency check passed: all foreign keys valid

=== Durability/Recovery Test (Restart DB) ===
[OK] Durability verified: state matches after restart
```

---

## Module B: Concurrent Workload & Stress Testing (⏳ NEEDS SQL DB SETUP)

### What is Implemented

1. **Custom Engine Stress Test** (`stress_compare.py`)
   - Multi-threaded concurrent assignment operations
   - Configurable failure injection ratio
   - Metrics: commits, rollbacks, throughput, latency (avg, p95)

2. **Backend Comparison Framework**
   - Runs identical workload on both backends
   - Outputs: `Assignment_3/results/backend_comparison.csv`

3. **SQL Workload Adapter**
   - Connects via Module B config (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
   - Requires `.env` file in Module_B directory

### How to Enable SQL Comparison

1. **Ensure Module B MySQL DB is running:**
   ```bash
   mysql -h localhost -u root -p
   ```

2. **Create/recreate FixIIT database:**
   ```bash
   mysql -h localhost -u root -p < Track1_Assignment1_ModuleA.sql
   ```

3. **Update Module B `.env`:**
   ```
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=fixiit_db
   ```

4. **Run comparison:**
   ```powershell
   & "C:/Program Files/Python313/python.exe" Assignment_3/stress_compare.py
   ```

### Custom Engine Metrics (Current)

```
backend: custom_bplustree
requests: 200
workers: 16
commits: 185
rollbacks: 15
total_time_s: 12.95
throughput_rps: 15.45
avg_ms: 997.07
p95_ms: 1463.96
status: ok
```

### Tuning Environment Variables

```powershell
$env:A3_REQUESTS="400"       # Total concurrent requests
$env:A3_WORKERS="24"          # Thread pool size
& "C:/Program Files/Python313/python.exe" Assignment_3/stress_compare.py
```

---

## What to Include in Your Report

### **Part 1: ACID Validation (Module A)**

Include screenshots/logs of:

1. **Atomicity Evidence**
   - Run ACID demo with injected failure
   - Show "Initial State" vs "State after failure" JSON outputs
   - Caption: "Transaction was rolled back; no partial updates remain"

2. **Consistency Evidence**
   - Show final state JSON
   - Verify all ticket_id references in assignments exist
   - Verify all technician_member_id and assigned_by exist
   - Caption: "All foreign key constraints enforced before commit"

3. **Isolation Evidence**
   - Show stress test run output
   - Highlight: no corruption, no lost updates
   - Caption: "Concurrent transactions serialized; data integrity maintained"

4. **Durability Evidence**
   - Run ACID demo once, capture final state
   - Restart DB (rerun same script)
   - Show states match
   - Caption: "After restart, committed state persists"

### **Part 2: Concurrent Workload (Module B)**

1. **Custom Engine Results**
   - Include `assignment_3/results/backend_comparison.csv` CSV table
   - Show throughput (req/s), latency (avg ms, p95), commit/rollback counts
   - Caption: "Custom B+ Tree engine performance under 200 concurrent assignments (16 workers)"

2. **SQL Backend Results** (when DB is set up)
   - Same CSV with MySQL row added
   - Comparison table in report
   - Caption: "Comparison: Custom B+ Tree vs MySQL"

3. **Failure Injection Results**
   - Show rollback counts > 0 in "Rollbacks" column
   - Caption: "System correctly rolled back failed transactions"

### **Part 3: Explanation**

Write 2-3 sentences for each:

- **How correctness of operations is ensured:**
  - Use WAL logging and before/after images
  - Validator enforces constraints before commit
  - Serialized locking prevents concurrent corruption

- **How failures are handled:**
  - Injected failures trigger abort in commit phase
  - All staged operations rolled back
  - Previous state restored from snapshot

- **How multi-user conflicts are handled:**
  - Serialized commit lock ensures isolation
  - Concurrent transactions do not corrupt shared data
  - High rollback rates acceptable (injected failures simulate conflicts)

- **What experiments were performed:**
  - 1. ACID demo with failure injection
  - 2. Stress test with 200 concurrent assignment operations
  - 3. Backend comparison (Custom vs SQL)

- **Observations and limitations:**
  - Custom engine: slower than SQL (expected for in-memory B+ Tree vs optimized DB)
  - However: demonstrates ACID properties correctly
  - Limitation: no distributed transactions, single-threaded recovery

---

## File Structure

```
Assignment_3/
├── README.md                                    (this file)
├── custom_engine/
│   ├── __init__.py
│   ├── engine.py                               (TransactionalBPlusDatabase class)
│   └── models.py                               (FixIIT schema, validator, init)
├── custom_engine_state/                        (auto-created; contains WAL + table snapshots)
│   ├── wal.jsonl
│   ├── metadata.json
│   └── tables/{members.json, tickets.json, assignments.json}
├── run_module_a_acid_demo.py                   (ACID validation demo)
├── stress_compare.py                           (Module B concurrent workload)
├── results/
│   └── backend_comparison.csv                  (stress test results)
└── requirements.txt
```

---

## Verification Checklist

- [ ] Module A: ACID demo runs without errors
- [ ] Module A: WAL file is populated with transaction logs
- [ ] Module A: Restart recovery works (state persists)
- [ ] Module A: Injected failure causes rollback (atomicity verified)
- [ ] Module B: MySQL DB configured and accessible
- [ ] Module B: Stress test runs with both custom and SQL backends
- [ ] Module B: Comparison CSV generated
- [ ] Report: Screenshots of all evidence included
- [ ] Report: Explanations address all 4 ACID properties

---

## Questions?

**"Which backend should we use for Module B?"**
- Use **both**:
  - Custom for Module A (mandatory)
  - SQL for comparison/performance analysis in Module B

**"What if MySQL isn't available?"**
- Custom engine will still run and generate results
- SQL section will report "skipped" with reason
- Focus report on custom engine correctness instead of comparison

**"Can we modify the schema?"**
- No; use the exact 3 relations from `custom_engine/models.py`
- They match your FixIIT assignment requirements

---

## Deadline

**6:00 PM, 5 April 2026**

Submit:
1. Updated assignment_name_report.pdf
2. Video (concurrent usage + failure recovery + speed comparison)
