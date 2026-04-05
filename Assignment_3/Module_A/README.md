# Module A - Transaction Engine and Crash Recovery

Module A extends the Assignment 2 custom B+ Tree database with transaction management, ACID validation, failure handling, and WAL-based recovery.

## Overview

This module demonstrates:

- Transaction API: `BEGIN`, `COMMIT`, `ROLLBACK`
- ACID properties across multiple relations
- Failure injection during transaction execution
- Write-ahead logging (WAL) and restart recovery
- Additional edge-case validation for robustness

## Core Design

### Storage Model

- One B+ Tree-backed table per relation
- Primary key is the B+ Tree key
- All operations update the B+ Tree representation directly

### Relations Used

- `members`
- `tickets`
- `assignments`

### Recovery Model

WAL records transaction lifecycle entries (`BEGIN`, `APPLY`, `COMMIT`, `ABORT`) with before/after record states. On restart:

- committed transactions are redone
- incomplete/aborted transactions are undone

## Repository Layout

| Path | Purpose |
|------|---------|
| `custom_engine/engine.py` | Transaction manager, WAL, recovery logic |
| `custom_engine/models.py` | Schema, validators, DB bootstrap |
| `custom_engine/__init__.py` | Module exports |
| `run_acid_demo.py` | Main ACID workflow (Atomicity, Consistency, Durability, Isolation) |
| `run_edge_cases.py` | Additional failure/recovery edge-case tests |
| `run_isolation_demo.py` | Legacy isolation-only helper script (optional) |
| `custom_engine_state/` | Runtime state (auto-generated) |
| `report/module_a_report.tex` | Module A LaTeX report |

## Quick Start

From repository root:

```powershell
cd Assignment_3/Module_A
Remove-Item -Path "custom_engine_state" -Recurse -Force -ErrorAction SilentlyContinue
python .\run_acid_demo.py
python .\run_edge_cases.py
```

## Expected Output Markers

After `run_acid_demo.py`:

- `[OK] Atomicity verified: partial transaction was rolled back`
- `[OK] Consistency check passed: all foreign keys valid`
- `[OK] Durability verified: state matches after restart`
- `[OK] Isolation check #1 passed: no dirty read`
- `[OK] Isolation check #2 passed: committed data is visible after commit`
- `[OK] All ACID checks completed`

After `run_edge_cases.py`:

- `PASS` for all listed edge cases
- `[OK] All edge cases completed`

## Storage Artifacts

`custom_engine_state/` is generated at runtime and typically contains:

- `wal.jsonl` - transaction log used for recovery
- `metadata.json` - schema/table metadata
- `tables/*.json` - persisted table snapshots

## Report and Video Evidence Checklist

For reporting or viva/demo, capture:

1. Initial state output (members, tickets, assignments)
2. Atomicity failure and rollback confirmation
3. Consistency success output
4. Durability restart confirmation
5. Isolation output (pre-commit visibility and post-commit visibility)
6. WAL excerpt (`BEGIN`, `APPLY`, `COMMIT`, `ABORT`)
7. Edge-case summary output

## Notes

- `custom_engine_state` should be cleared before a fresh demonstration run.
- Module A focuses on correctness and recovery; large-scale load testing is handled in Module B.
