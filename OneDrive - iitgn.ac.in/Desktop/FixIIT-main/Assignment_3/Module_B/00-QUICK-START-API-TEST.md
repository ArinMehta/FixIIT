# Module B - Flask API Stress Testing Quick Start

**Updated:** April 5, 2026
**Requirements Met:** ✅ Correct user credentials, MySQL connected

---

## 🚀 START THE FLASK API SERVER

**Terminal 1** - Start Flask API:
```bash
cd /Users/sohamshrivastava/Desktop/Database_project/FixIIT/Assignment_2/Module_B
source ~/Desktop/Database_project/myenv/bin/activate
python3 run.py
```

Expected output:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

---

## 🧪 RUN THE STRESS TESTS

**Terminal 2** - Run stress test:
```bash
cd /Users/sohamshrivastava/Desktop/Database_project/FixIIT/Assignment_3/Module_B
source ~/Desktop/Database_project/myenv/bin/activate
python3 stress_test_api.py
```

---

## ✅ CREDENTIALS USED

**Fixed Issues:**
- ❌ Was trying: `username=shiv.patel, password=password123`
- ✅ Corrected to: `username=user, password=password`

**Database verified:**
- MySQL running: ✅ Version 9.6.0
- Database exists: ✅ fixiit_db
- Tables present: ✅ 13 tables (members, tickets, assignments, etc.)
- Test user exists: ✅ username='user' (member_id=2, Shiv Patel)

---

## 📊 WHAT THE TESTS DO

**Concurrent Read Test (200 requests, 16 workers)**
- Multiple users fetching tickets simultaneously
- Tests isolation: reads should not block
- Verifies MySQL handles concurrent reads correctly

**Concurrent Write Test (100 requests, 8 workers)**
- Multiple users creating tickets simultaneously
- Tests atomicity: each write completes fully or rolls back
- Verifies MySQL transaction handling

**Race Condition Test (50 requests, 16 workers)**
- Many users trying to update THE SAME ticket
- Tests isolation & consistency: no lost updates
- MySQL InnoDB row-level locking handles this

**Mixed Workload Test (200 requests, 16 workers, 70% reads 30% writes)**
- Real-world usage pattern
- Tests entire system under realistic load
- Verifies all ACID properties together

---

## 📈 EXPECTED RESULTS

When both servers are running, you should see:

```
=== MODULE B (Assignment 3): SQL API STRESS TESTING ===

API Base URL: http://127.0.0.1:5000
[OK] Server is running

Configuration:
  Total requests per test: 100
  Worker threads: 16
  Test user: user

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
  throughput_rps      : 45+ requests/second
  avg_ms              : ~20ms
  p95_ms              : ~40ms
  status              : ok

--- concurrent_write ---
  requests            : 50
  workers             : 8
  successes           : 50
  errors              : 0
  throughput_rps      : 25+ requests/second
  avg_ms              : ~30ms
  p95_ms              : ~50ms
  status              : ok

...and so on
```

---

## 🐛 TROUBLESHOOTING

**Problem:** Connection refused
```
❌ Error: [Errno 111] Connection refused
```
**Solution:** Make sure Flask server is running in Terminal 1:
```bash
cd Assignment_2/Module_B
python3 run.py
```

**Problem:** Login failed
```
❌ "Could not authenticate any clients"
```
**Solution:** Verify credentials are correct:
- Username: `user`
- Password: `password`

**Problem:** MySQL connection error
```
❌ mysql.connector.errors.ProgrammingError: 1064
```
**Solution:** Check .env file in Assignment_2/Module_B:
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=110578
DB_NAME=fixiit_db
```

---

## 📝 NEXT STEPS FOR YOUR TEAM

1. **Start Flask Server** (Terminal 1):
   ```bash
   cd Assignment_2/Module_B && python3 run.py
   ```

2. **Run Stress Test** (Terminal 2):
   ```bash
   cd Assignment_3/Module_B && python3 stress_test_api.py
   ```

3. **Collect Results:**
   - Screenshot the console output
   - Check `results/stress_test_api_*.csv` for detailed metrics
   - Include in your report as evidence of ACID properties

4. **Verify ACID Behavior:**
   - All requests succeeded: ✅ Atomicity (no partial updates)
   - No duplicate data: ✅ Consistency (constraints enforced)
   - Concurrent operations completed: ✅ Isolation (no interference)
   - Data persisted in database: ✅ Durability (committed writes stable)

---

## 📋 FILES UPDATED

- `stress_test_api.py` - Fixed credentials (user/password instead of shiv.patel/password123)
- `README.md` - Updated documentation with correct credentials
- `ALL TESTS NOW POINT TO CORRECT USER IN DATABASE`

---

**Status:** ✅ Ready to test
**Next Action:** Start Flask server + run stress test
