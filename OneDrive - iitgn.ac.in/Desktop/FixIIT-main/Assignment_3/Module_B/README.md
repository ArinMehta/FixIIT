# Module B: Concurrent Workload & Stress Testing

**Status:** ⏳ READY (MySQL setup required)

This module tests ACID behavior under concurrent multi-user load and failure conditions.

## What Module B Addresses

### Core Requirements Met

1. **Multi-User Simulation**
   - 16 concurrent worker threads (configurable)
   - 200+ concurrent requests (configurable)
   - Each simulates independent user performing ticket assignment

2. **Race Condition Testing**
   - Same ticket assignment attempted concurrently
   - Same technician assigned multiple tasks
   - Stress tests serialized locking correctness

3. **Failure Under Load**
   - 10% of transactions injected with failures
   - Rollback during concurrent operations
   - Verify no data corruption under failure

4. **Stress Metrics**
   - Throughput (requests/second)
   - Latency (average ms, p95 ms)
   - Commit/rollback counts
   - Success rate

5. **Backend Comparison**
   - Custom B+ Tree engine baseline
   - SQL (MySQL) optional comparison
   - Side-by-side performance results

## Files

| File | Purpose |
|------|---------|
| `stress_compare.py` | Concurrent workload + comparison (~200 lines) |
| `results/backend_comparison.csv` | Benchmark results (auto-generated) |

## Run Module B (Custom Engine Only)

```powershell
cd Assignment_3/Module_B
"C:\\Program Files\\Python313\\python.exe" stress_compare.py
```

## Run Module B (With SQL Comparison)

**Prerequisites:**
1. MySQL running: `mysql -h localhost -u root -p`
2. FixIIT database loaded: `mysql < ../../../Track1_Assignment1_ModuleA.sql`
3. Module_B/.env configured:
   ```
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=fixiit_db
   ```

**Run:**
```powershell
cd Assignment_3/Module_B
"C:\\Program Files\\Python313\\python.exe" stress_compare.py
```

## Tuning Parameters

```powershell
# Custom workload size
$env:A3_REQUESTS="400"      # Total concurrent requests (default 200)
$env:A3_WORKERS="32"         # Thread pool size (default 16)

"C:\\Program Files\\Python313\\python.exe" stress_compare.py
```

## Expected Output

### Custom Engine Results

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

**Interpretation:**
- 92.5% success rate (185/200 commits)
- 7.5% rollback rate (15/200, mostly due to injected failures)
- ~997ms average latency (expected due to serialized lock)
- p95 (95th percentile) ~1464ms

### SQL Backend Results (if available)

```
backend: mysql_sql
requests: 200
workers: 16
errors: 0
total_time_s: 20.33
throughput_rps: 9.84
avg_ms: 1608.00
p95_ms: 2385.09
status: ok
```

**Interpretation:**
- 0% errors (SQL handles crashes via constraints)
- Slower throughput (network + connection overhead)
- Higher latency (query parsing + planning)

### Comparison CSV

**Location:** `results/backend_comparison.csv`

```csv
backend,requests,workers,commits,rollbacks,total_time_s,throughput_rps,avg_ms,p95_ms,status
custom_bplustree,200,16,185,15,12.946965,15.448,997.071,1463.964,ok
mysql_sql,200,16,0,0,20.328034,9.839,1608.002,2385.093,ok
```

## Workload Details

### What Each Request Does

```python
transaction:
  1. get member by ID (verify exists)
  2. get ticket by ID (verify exists)
  3. update ticket status (assign in progress)
  4. insert assignment record (new technician assignment)
  
outcome:
  - success → COMMIT (all 4 changes persisted)
  - 10% chance → injected failure (ROLLBACK, no changes)
```

### Concurrency Pattern

```
Thread-1  [BEGIN] update ticket→1 [COMMIT]
Thread-2           [BEGIN] update ticket→1 [conflict!] [COMMIT]
          ↓         ↓      ↓              ↓
          t0        t1     t2             t3

expected: serialized execution, no corruption
          one succeeds, other waits (locked) then either succeeds or rolls back
```

## For Your Team

### Running Locally

1. Module B works independently (no SQL required to run basic version)
2. Custom engine produces metrics immediately
3. SQL metrics optional (skip if MySQL unavailable)

### Collecting Evidence

1. Run with default settings, capture output
2. Run with higher load if reporting on performance:
   ```powershell
   $env:A3_REQUESTS="500"; $env:A3_WORKERS="32"
   ```
3. Capture CSV results

### Report Sections

- **Isolation:** Show concurrent commits without corruption
- **Atomicity:** Show rollback counts from injected failures
- **Performance:** Include custom vs SQL comparison
- **Scalability:** Note throughput/latency under load

## Edge Cases Covered

| Case | Expected | Evidence |
|------|----------|----------|
| 10% requests fail | Rollbacks > 0 | rollbacks column in CSV |
| Concurrent same-ticket | Only one succeeds | Status remains consistent |
| Concurrent different-tickets | Both succeed | No corruption in state |
| Long-running + short | No starvation | Throughput maintained |
| High latency p95 | Within 2x avg | p95_ms < 2x avg_ms |

## Technical Details

### Failure Injection

```python
fail_injected = random.random() < 0.1  # 10% failure rate
fail_after_ops = 2 if fail_injected else None
tx.commit(fail_after_ops=fail_after_ops)
# After 2 operations: RuntimeError("Injected failure")
# → ROLLBACK triggered
```

### Locking Behavior

All 200 requests try to touch ticket_id = ((i % 3) + 1), so multiple threads contend on same ticket_id.

Serialized lock in engine.py ensures:
- Only one commit at a time
- No lost updates
- No dirty reads

## Next Steps

1. **Setup:** Configure Module_B/.env if available
2. **Run:** Execute stress_compare.py
3. **Collect:** Save CSV + console output
4. **Report:** Include results and interpretation

---

**Run time:** 10-30 seconds depending on load
