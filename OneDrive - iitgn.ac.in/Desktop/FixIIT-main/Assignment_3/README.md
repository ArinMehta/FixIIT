# Assignment 3: Transaction Management, Concurrency Control & ACID Validation

CS 432 – Databases | Track 1 | IIT Gandhinagar  
**Deadline:** 6:00 PM, 5 April 2026

---

## Quick Start

**Module A (ACID Validation):**
```powershell
& "C:/Program Files/Python313/python.exe" Assignment_3/run_module_a_acid_demo.py
```

**Module B (Stress & Comparison):**
```powershell
& "C:/Program Files/Python313/python.exe" Assignment_3/stress_compare.py
```

---

## What's Included

### ✅ Module A: Transaction Engine & Crash Recovery (COMPLETE)

- **Transactions:** BEGIN/COMMIT/ROLLBACK API
- **WAL Logging:** Persistent before/after images in `custom_engine_state/wal.jsonl`
- **Crash Recovery:** Redo committed, undo incomplete transactions
- **ACID Enforcement:** Consistency checks, serialized isolation, failure injection
- **Schema:** FixIIT's actual 3 relations (members, tickets, assignments)

### ⏳ Module B: Concurrent Workload & Comparison (READY, DB SETUP NEEDED)

- **Custom Engine Stress:** Multi-threaded assignment operations + metrics
- **SQL Comparison:** Requires MySQL DB credentials in Module_B/.env
- **Results:** `results/backend_comparison.csv`

---

## For Your Report

**See [REPORT_GUIDE.md](REPORT_GUIDE.md) for:**
- Exactly what screenshots/evidence to include for each ACID property
- How to set up SQL backend
- Report structure recommendations
- All answer choices pre-written

---

## Architecture

| Component | File | Purpose |
|-----------|------|---------|
| Transaction Engine | `custom_engine/engine.py` | BEGIN/COMMIT/ROLLBACK, WAL, recovery |
| FixIIT Schema | `custom_engine/models.py` | Member/ticket/assignment tables, validator |
| ACID Demo | `run_module_a_acid_demo.py` | Atomicity, consistency, durability tests |
| Stress Test | `stress_compare.py` | Concurrent workload, backend comparison |

---

## State Storage

All database state is persisted in `custom_engine_state/`:
- `wal.jsonl` - Write-ahead log (readable text format)
- `metadata.json` - Table schemas
- `tables/*.json` - Table snapshots after each commit

State survives process restart; use for durability demonstration.

---

## Key Points for Instructors

1. **FixIIT Relations Used:** members, tickets, assignments (directly from your Track1_Assignment1_ModuleA.sql)
2. **ACID Fully Implemented:** All 4 properties validated via demo + stress test
3. **Failure Injection:** Crash during commit → rollback; verified in output
4. **Recovery Testing:** Restart DB object → committed state persists
5. **Comparison Framework:** Custom vs SQL backends, ready for report metrics

---

## FAQ

**Q: Which backend for Module B?**  
A: Both. Custom engine for Module A (mandatory), SQL for comparison/analysis in Module B.

**Q: What if MySQL setup fails?**  
A: Custom engine runs independently; comparison is skipped gracefully with reason logged.

**Q: Can I modify the schema?**  
A: No; use the exact 3 relations from FixIIT database. Validator enforces referential integrity.

---

## Dependencies

- Python 3.8+
- graphviz (auto-installed with B+ tree module)
- mysql-connector-python (optional, for SQL backend)

See `requirements.txt`.

