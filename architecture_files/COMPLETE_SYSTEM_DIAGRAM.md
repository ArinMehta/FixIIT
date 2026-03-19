# Module B Implementation - The Complete Picture

## 🎯 EXECUTIVE SUMMARY

We're building a **simple Flask web application** that:
1. **Authenticates users** with username/password (converts to JWT token)
2. **Shows dashboards** personalized for regular users and admins
3. **Manages permissions** (regular users only see their own, admins see all)
4. **Logs everything** (every API call, every attempt, success/failure)
5. **Optimizes queries** (database indexes make it 50x faster)

**Total code: ~1200 lines. Total time: ~13 hours. Complexity: LOW.**

---

## 🌟 Why This Approach Works

### Problem: Web Apps Are Complex
- Authentication is messy
- Permissions are confusing
- Databases are slow
- Security is hard

### Our Solution: Keep It Simple
```
✓ JWT tokens (not sessions)
✓ Decorators for permissions (not complex logic)
✓ Indexes on database (not complicated queries)
✓ Logging everything (security = visibility)
```

---

## 📊 The Complete System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER'S BROWSER                             │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  login.html (Form: username + password)                     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                          │                                           │
│                          ↓                                           │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  JavaScript:                                                 │  │
│  │  1. Get username/password from form                          │  │
│  │  2. Send to server: POST /login                             │  │
│  │  3. Receive JWT token back                                  │  │
│  │  4. Store in localStorage                                   │  │
│  │  5. Redirect to dashboard.html                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  dashboard.html (Shows tickets in table)                    │  │
│  │                                                              │  │
│  │  JavaScript:                                                │  │
│  │  1. Add JWT to request header                               │  │
│  │  2. Send GET /tickets                                       │  │
│  │  3. Receive tickets JSON                                    │  │
│  │  4. Display in HTML table                                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ↓ HTTP with JWT in header
┌─────────────────────────────────────────────────────────────────────┐
│                      FLASK WEB SERVER (run.py)                       │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  api.py - HTTP Routes                                       │  │
│  │  ├─ POST /login (no auth needed)                            │  │
│  │  ├─ GET /isAuth (verify token works)                        │  │
│  │  ├─ GET /tickets @login_required                            │  │
│  │  ├─ POST /tickets @login_required                           │  │
│  │  ├─ PUT /tickets/<id> @admin_required                       │  │
│  │  ├─ DELETE /tickets/<id> @admin_required                    │  │
│  │  └─ GET / (welcome page)                                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  auth.py - JWT Token Management                             │  │
│  │  ├─ generate_token(user_id, role)                           │  │
│  │  │   Creates JWT: {user_id: 5, role: "admin", exp: ...}    │  │
│  │  │   Returns: "eyJhb..." (signed by SECRET_KEY)            │  │
│  │  └─ verify_token(token)                                     │  │
│  │      Checks signature is valid                              │  │
│  │      Checks not expired                                      │  │
│  │      Returns: {user_id: 5, role: "admin"}                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  rbac.py - Permission Checks                                │  │
│  │  ├─ @login_required decorator                               │  │
│  │  │   Checks: Is there a valid JWT? If no → 401              │  │
│  │  ├─ @admin_required decorator                               │  │
│  │  │   Checks: Is JWT valid? Is role = "admin"? If no → 403   │  │
│  │  └─ check_permission(user_id, action)                       │  │
│  │      Checks: Can user_5 delete ticket_2?                    │  │
│  │      Logic: if admin YES, if owner YES, else NO              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  database.py - MySQL Connection                             │  │
│  │  Function: execute_query(sql, params)                       │  │
│  │  ├─ Connects to MySQL                                       │  │
│  │  ├─ Executes SQL query                                      │  │
│  │  ├─ Returns: List of rows                                   │  │
│  │  └─ Closes connection                                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  audit_logger.py - Logging                                  │  │
│  │  Function: log_api_call(user_id, endpoint, status, msg)     │  │
│  │  Writes to: logs/audit.log                                  │  │
│  │  Format: [timestamp] USER_ID | ENDPOINT | STATUS | MESSAGE   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ↓ SQL Query
┌─────────────────────────────────────────────────────────────────────┐
│                        MYSQL DATABASE                               │
│                                                                      │
│  Tables:                                       Indexes:             │
│  ├─ users                                      ├─ users.username    │
│  │ (id, username, password_hash, ...)         ├─ tickets.user_id   │
│  │                                             └─ tickets.status_id │
│  ├─ roles                                                           │
│  │ (id, role_name)                                                 │
│  │                                                                  │
│  ├─ user_roles (links users to roles)                              │
│  │                                                                  │
│  └─ tickets (from Assignment 1 FixIIT schema)                      │
│  │ (ticket_id, title, user_id, status_id, ...)                    │
│                                                                      │
│  Sample query (with index):                                         │
│  SELECT * FROM tickets WHERE user_id = 5                           │
│  Time: 5ms (fast, with index)                                       │
│  Time: 250ms (slow, without index)                                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Actual Request Example: User Logs In

```
BROWSER:
User types username="john" password="secret123" → clicks Login

    ↓ 

JavaScript reads form → fetch("POST /login", {username, password})

    ↓

FLASK SERVER (api.py):
@app.route('/login', methods=['POST'])
def login():
    username = request.json['username']
    password = request.json['password']
    
    ↓
    
    # Check credentials in database (database.py)
    query = "SELECT * FROM users WHERE username = %s"
    user = execute_query(query, (username,))
    
    if user and verify_password(password, user['password_hash']):
        ✓ Valid credentials
        
        ↓
        
        # Generate JWT token (auth.py)
        token = generate_token(
            user_id=user['id'],
            role=user['role']
        )
        
        ↓
        
        # Log this action (audit_logger.py)
        log_api_call(
            user_id=user['id'],
            endpoint='/login',
            status='SUCCESS',
            message='User logged in'
        )
        
        ↓
        
        # Send token to browser
        return {
            'message': 'Login successful',
            'session_token': token
        }
    else:
        ✗ Invalid credentials
        
        ↓
        
        # Log the failed attempt
        log_api_call(
            user_id=None,
            endpoint='/login',
            status='FAILED',
            message='Invalid credentials'
        )
        
        ↓
        
        return {'error': 'Invalid credentials'}, 401

    ↓

BROWSER:
Receives token → stores in localStorage → redirects to dashboard
```

---

## 🔄 Actual Request Example: User Fetches Tickets

```
BROWSER:
User on dashboard.html → JavaScript calls:
fetch("GET /tickets", {
    headers: {
        'Authorization': 'Bearer eyJhb...' (JWT token)
    }
})

    ↓

FLASK SERVER (api.py):
@app.route('/tickets', methods=['GET'])
@login_required  # Decorator checks JWT
def get_tickets():
    # At this point, JWT is verified (rbac.py handled it)
    user_id = get_current_user_id()  # Extracted from JWT
    
    ↓
    
    # Query database
    query = "SELECT * FROM tickets WHERE user_id = %s"
    tickets = execute_query(query, (user_id,))
    
    ↓
    
    # Log the action
    log_api_call(
        user_id=user_id,
        endpoint='/tickets',
        status='SUCCESS',
        message='Fetched 3 tickets'
    )
    
    ↓
    
    return {'tickets': tickets}

    ↓

BROWSER:
Receives tickets JSON → displays in table
```

**audit.log now contains:**
```
[2024-03-18 14:32:45] USER_1 | GET /tickets | SUCCESS | Fetched 3 tickets
```

---

## 🔓 What Happens When Someone Tries to Cheat

```
Hacker tries: DELETE /tickets/1 without JWT token

    ↓

FLASK SERVER (api.py):
@app.route('/tickets/<id>', methods=['DELETE'])
@admin_required  # Checks JWT is present
def delete_ticket(id):
    # Never reaches here
    
In rbac.py, @admin_required does:
1. Check request headers for 'Authorization'
2. NOT FOUND!
3. Raise: "Unauthorized - no token"
4. Return: 401 Unauthorized

    ↓

BROWSER:
Gets 401 error

    ↓

audit.log contains:
[2024-03-18 14:35:20] UNKNOWN | DELETE /tickets/1 | FAILED | No token provided
```

---

## 📋 What Gets Built (13 Files)

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| config.py | Settings | ~40 | ✅ DONE |
| requirements.txt | Dependencies | ~5 | ✅ DONE |
| run.py | Entry point | ~10 | ✅ DONE |
| app/__init__.py | Flask setup | ~30 | ⏳ NEXT |
| app/database.py | MySQL connector | ~80 | ⏳ NEXT |
| app/models.py | User/Role classes | ~60 | ⏳ NEXT |
| app/auth.py | JWT logic | ~70 | ⏳ NEXT |
| app/rbac.py | Permissions | ~40 | ⏳ NEXT |
| app/audit_logger.py | Logging | ~50 | ⏳ NEXT |
| app/api.py | REST endpoints | ~150 | ⏳ NEXT |
| app/templates/*.html | HTML pages | ~200 | ⏳ NEXT |
| sql/*.sql | Database setup | ~100 | ⏳ NEXT |
| performance_test.py | Benchmarking | ~100 | ⏳ LATER |
| **TOTAL** | | **~1035** | |

---

## ✅ Success Criteria

When Module B is complete, you'll have:

1. **Working Web App**
   - [ ] Login page works
   - [ ] Can login with username/password
   - [ ] Dashboard shows your tickets
   - [ ] Logout works

2. **Security**
   - [ ] JWT tokens validated
   - [ ] Permissions enforced
   - [ ] Unauthorized attempts blocked
   - [ ] Audit log has entries

3. **Performance**
   - [ ] Queries execute fast (with indexes)
   - [ ] Performance report shows 50x+ improvement
   - [ ] Database optimized

4. **Documentation**
   - [ ] Code has comments
   - [ ] IMPLEMENTATION_REPORT.md explains everything
   - [ ] README has setup instructions

5. **Demonstration**
   - [ ] Video shows all features working
   - [ ] Video shows RBAC in action
   - [ ] Video shows logging working

---

## 🎓 Understanding the Architecture

### The 4-Layer Model

```
Layer 4: Browser (User sees HTML/CSS)
         ↕ HTTP + JWT token
Layer 3: Flask API (Python processes requests)
         ↕ SQL queries
Layer 2: Database (MySQL stores data)
         ↕ Optimization
Layer 1: Indexes (Makes queries fast)
```

Each layer is independent:
- Browser doesn't care how database works
- Database doesn't care how HTML looks
- API acts as translator between browser and database

---

## 🎯 Next Steps

**When you're ready, tell me:**
- "Start Phase 2" → Build database layer (database.py, models.py, SQL files)
- "Questions on architecture?" → I'll explain any part in more detail
- "Show me examples?" → I'll show code snippets for any component

**Each phase will have:**
1. Full implementation of that phase
2. Comments explaining every function
3. Examples of how to use it
4. Instructions to test it

Simple, working code. No surprises. No complexity.

Let's build this! 🚀
