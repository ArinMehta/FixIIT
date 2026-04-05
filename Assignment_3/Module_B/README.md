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
- **Password:** `user123`

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
