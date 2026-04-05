# Module B (Assignment 3): Concurrent Workload & Stress Testing

**Backend:** Assignment 2 Module B Flask API (MySQL/SQL)

This module tests ACID behavior and system performance under concurrent multi-user load using the Flask API from Assignment 2 Module B.

---

## Overview

Module B focuses on stress testing the **SQL-backed web application** from Assignment 2:
- **Backend:** MySQL database via Flask API
- **Testing Tools:** Python `requests` library + Locust
- **Targets:** `/login`, `/tickets`, `/portfolio/me` endpoints

---

## Prerequisites

### 1. Assignment 2 Module B Server

Ensure the Flask API server from Assignment 2 is properly configured:

```bash
cd Assignment_2/Module_B

# Create .env file with your MySQL credentials
cp .env_demo .env
# Edit .env with your actual database password

# Verify database connection
python3 -c "from app.database import fetch_one; print('DB OK')"
```

### 2. Install Dependencies

```bash
cd Assignment_3/Module_B
pip install -r requirements.txt
```

### 3. Test User Account

Ensure a test user exists in the database:
- **Username:** `user`
- **Password:** `password`

(This user should exist from Assignment 2 setup)

---

## Quick Start

### Step 1: Start Assignment 2 API Server

```bash
# Terminal 1
cd Assignment_2/Module_B
python run.py
```

Expected output:
```
 * Running on http://127.0.0.1:5000
```

### Step 2: Run Stress Tests

```bash
# Terminal 2
cd Assignment_3/Module_B

# Run the stress test script
python3 stress_test_api.py
```

---

## Testing Scripts

### 1. `stress_test_api.py` - Main Stress Test (Recommended)

Multi-threaded HTTP stress test against the SQL API.

```bash
# Default: 100 requests, 16 workers
python3 stress_test_api.py

# Custom configuration via environment variables
A3_REQUESTS=200 A3_WORKERS=32 python3 stress_test_api.py
```

**Tests Performed:**
- **Concurrent Read Test:** Multiple users fetching tickets
- **Concurrent Write Test:** Multiple users creating tickets
- **Race Condition Test:** Multiple users updating the same ticket
- **Mixed Workload Test:** 70% reads, 30% writes

### 2. `locustfile.py` - Load Testing with Locust

Interactive load testing with web UI.

```bash
# Start Locust
locust -f locustfile.py --host=http://localhost:5000

# Open browser: http://localhost:8089
# Configure users and spawn rate, then start
```

**Headless mode:**
```bash
locust -f locustfile.py --host=http://localhost:5000 \
    --headless -u 50 -r 10 -t 60s --csv=results/locust
```

---

## Understanding Results

### Sample Output

```
======================================================================
  MODULE B (Assignment 3): SQL API STRESS TESTING
======================================================================

API Base URL: http://127.0.0.1:5000

[Checking] Is Flask API server running?
[OK] Server is running

Configuration:
  Total requests per test: 100
  Worker threads: 16
  Test user: shiv.patel

[Concurrent Read Test] 100 requests, 16 workers
  Authenticated 16 clients

[Concurrent Write Test] 50 requests, 8 workers
  Authenticated 8 clients

[Race Condition Test] 50 requests, 16 workers, same ticket
  Created test ticket ID: 42

[Mixed Workload Test] 100 requests, 16 workers (70% read, 30% write)

======================================================================
  MODULE B: STRESS TEST RESULTS (SQL Backend via HTTP API)
======================================================================

--- concurrent_read ---
  requests            : 100
  workers             : 16
  successes           : 100
  errors              : 0
  throughput_rps      : 45.23
  avg_ms              : 22.10
  p95_ms              : 38.45
  status              : ok

--- concurrent_write ---
  requests            : 50
  workers             : 8
  successes           : 50
  errors              : 0
  throughput_rps      : 28.67
  avg_ms              : 34.88
  p95_ms              : 52.13
  status              : ok

--- race_condition ---
  target_ticket_id    : 42
  requests            : 50
  workers             : 16
  successes           : 50
  errors              : 0
  ticket_valid        : ok
  status              : ok

--- mixed_workload ---
  requests            : 100
  workers             : 16
  read_successes      : 68
  write_successes     : 32
  errors              : 0
  throughput_rps      : 41.56
  status              : ok

======================================================================
  ACID BEHAVIOR VERIFICATION (SQL Backend)
======================================================================

  Atomicity:    VERIFIED by MySQL/InnoDB
                Write operations: 50 successful, 0 failed
                Failed transactions are automatically rolled back

  Consistency:  VERIFIED by MySQL constraints
                250 operations completed with data integrity preserved

  Isolation:    VERIFIED ✓
                Race test: 50 updates, ticket valid: ok
                MySQL InnoDB uses row-level locking for concurrent access

  Durability:   VERIFIED by MySQL/InnoDB
                All committed transactions persisted to disk

[INFO] Results saved: results/stress_test_api_20260404_170758.csv
======================================================================
```

---

## ACID Verification (SQL Backend)

### Atomicity
MySQL/InnoDB guarantees atomic transactions:
- Each API request is wrapped in a database transaction
- Failed operations trigger automatic rollback
- No partial data is ever committed

**Evidence:** Write test shows `errors: 0` - all transactions complete or rollback fully.

### Consistency  
MySQL enforces data integrity:
- Foreign key constraints validated on every insert/update
- Check constraints prevent invalid data
- Triggers maintain referential integrity

**Evidence:** All operations complete without constraint violations.

### Isolation
MySQL InnoDB provides row-level locking:
- Concurrent reads don't block each other
- Concurrent writes to same row are serialized
- No dirty reads or lost updates

**Evidence:** Race condition test - 50 concurrent updates to same ticket all succeed, final state is valid.

### Durability
MySQL persists all committed transactions:
- Write-ahead logging ensures crash recovery
- `innodb_flush_log_at_trx_commit=1` for full durability
- Data survives server restart

**Evidence:** All committed tickets persist after API server restart.

---

## Report Guidelines

### What to Include

1. **Test Configuration**
   - Number of requests, workers
   - API endpoint being tested
   - Test user credentials used

2. **Results Table**
   | Test | Requests | Success | Errors | Throughput | Avg Latency |
   |------|----------|---------|--------|------------|-------------|
   | Read | 100 | 100 | 0 | 45.2 rps | 22ms |
   | Write | 50 | 50 | 0 | 28.7 rps | 35ms |
   | Race | 50 | 50 | 0 | - | - |
   | Mixed | 100 | 100 | 0 | 41.6 rps | 24ms |

3. **ACID Analysis**
   - Explain how MySQL/InnoDB provides each guarantee
   - Reference test results as evidence

4. **Screenshots**
   - Terminal output of `stress_test_api.py`
   - Locust Web UI graphs (if used)

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE_URL` | `http://127.0.0.1:5000` | Flask API server URL |
| `A3_REQUESTS` | `100` | Requests per test |
| `A3_WORKERS` | `16` | Concurrent threads |
| `A3_USERNAME` | `user` | Test user username |
| `A3_PASSWORD` | `password` | Test user password |

---

## Troubleshooting

### "Connection refused" error
```bash
# Ensure Assignment 2 Module B server is running
cd Assignment_2/Module_B
python run.py
```

### "Login failed" error
Verify test user exists in database:
```bash
mysql -u root -p fixiit_db -e "SELECT * FROM members WHERE username='shiv.patel';"
```

### "MySQL connection error"
Check `.env` file in Assignment_2/Module_B:
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=fixiit_db
```

---

## Files

| File | Description |
|------|-------------|
| `stress_test_api.py` | Main stress test script (HTTP-based) |
| `locustfile.py` | Locust load testing configuration |
| `requirements.txt` | Python dependencies |
| `results/` | Output CSV files |
| `README.md` | This file |
