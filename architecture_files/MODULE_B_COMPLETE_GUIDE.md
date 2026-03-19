# Module B - Complete Implementation Guide

## 📌 Quick Summary: What We're Building

You want to build a **web application** for the FixIIT maintenance system where:
- ✅ Users can login with username/password
- ✅ After login, they see their own tickets
- ✅ Admins can manage all tickets and users
- ✅ Every action is logged to audit.log
- ✅ The system is fast (using database indexes)
- ✅ Code is simple and easy to understand

**No complex patterns. No fancy frameworks. Just clean, working code.**

---

## 🎯 The Approach in 3 Sentences

1. **Database Layer**: Create simple MySQL tables for users, roles, and sessions. Use indexes on frequently queried columns.
2. **Authentication**: Use JWT tokens (signed tokens containing user ID & role) that the browser stores and sends with every API request.
3. **API + UI**: Simple Flask backend with REST endpoints, paired with a basic HTML frontend that calls those endpoints.

---

## 🏗️ Architecture: How It All Works

### Layer 1: Browser (User Side)
```
User types username/password → clicks Login
        ↓
Browser sends to /login endpoint
```

### Layer 2: Backend (Server Side)
```
Flask receives POST /login
        ↓
Checks username/password in MySQL
        ↓
If valid → Creates JWT token (signed proof: "user 5 is logged in as admin")
        ↓
Sends JWT back to browser
        ↓
Browser stores JWT in localStorage (like browser memory)
```

### Layer 3: Subsequent Requests
```
User clicks "Get My Tickets"
        ↓
Browser automatically adds JWT to request header:
   "Hey server, here's user 5's proof that they're logged in"
        ↓
Server checks JWT:
   "Yes, this is valid. User 5 is admin."
        ↓
Server queries MySQL: "Get tickets for user 5"
        ↓
Server returns tickets in JSON
        ↓
Browser displays tickets in dashboard
```

### Layer 4: Database (Data Side)
```
MySQL stores:
- Users: (id, username, password_hash)
- Roles: (id, role_name like 'admin' or 'user')
- User_Roles: Links users to roles (many-to-many)
- Tickets: (from Assignment 1)

Indexes on: users.username, tickets.user_id
Why? These are used constantly in WHERE clauses
Result: Queries run 50x faster!
```

---

## 📂 Files We'll Create (Minimal Design)

### **13 Core Files You'll Write:**

```
config.py              ← Database credentials & settings
run.py                 ← Start the app

app/__init__.py        ← Initialize Flask
app/database.py        ← Talk to MySQL
app/models.py          ← User/Role classes
app/auth.py            ← Generate/verify JWT tokens
app/rbac.py            ← Check permissions (admin? user?)
app/api.py             ← 7 HTTP endpoints (/login, /isAuth, /tickets, etc.)
app/audit_logger.py    ← Write to audit.log

app/templates/base.html       ← HTML base template
app/templates/login.html      ← Login page
app/templates/dashboard.html  ← Tickets page

sql/create_tables.sql      ← Create users, roles tables
sql/insert_sample_data.sql ← Add test users
sql/create_indexes.sql     ← Add indexes

IMPLEMENTATION_REPORT.md   ← Explain everything
performance_test.py        ← Benchmark indexes
```

**That's it. 13 files totaling ~1200 lines of code.**

---

## 🔑 Key Design Decisions (Why Simple Matters)

### Decision 1: Use JWT Instead of Sessions
❌ **Complex Way**: Store sessions in database, check database on every request (slow)
✅ **Simple Way**: JWT token contains "user_id=5, role=admin" (signed by server key)
   - Client stores token locally
   - Client sends token with every request
   - Server only needs to verify signature (no database lookup!)
   - Stateless = scalable

### Decision 2: No ORM, Just Write SQL
❌ **Complex Way**: `User.objects.filter(id=5).update(role='admin')`
✅ **Simple Way**: `cursor.execute("UPDATE users SET role='admin' WHERE id=5")`
   - Anyone can read and understand the SQL
   - Easy to debug
   - Easy to optimize

### Decision 3: Minimal Frontend (HTML + Vanilla JavaScript)
❌ **Complex Way**: React, Redux, Webpack build process
✅ **Simple Way**: HTML forms + fetch() API calls
   - No build process
   - Few dependencies
   - Easy to modify

### Decision 4: One Function = One Query
❌ **Complex Way**: Generic database layer that builds queries dynamically
✅ **Simple Way**: 
   ```python
   def get_user_tickets(user_id):
       query = "SELECT * FROM tickets WHERE user_id = %s"
       return execute_query(query, (user_id,))
   ```
   - Crystal clear what data is returned
   - Easy to add indexes
   - Easy to optimize

---

## 🔐 Security in Plain English

### 1. Login Process
```
User enters password "mypassword123"
    ↓
Server hashes password with SHA256 → "x7f9k2l8m1n..."
    ↓
Compares with stored hash in database
    ↓
If match → Creates JWT token
    ↓
JWT contains: {user_id: 5, role: "admin", expiry: "2024-03-19"}
    ↓
Signs JWT with secret key (server only knows this)
    ↓
Sends token to browser
```

### 2. Every API Call After Login
```
Browser sends: GET /tickets
Header: Authorization: Bearer eyJhb... (JWT token)
    ↓
Server receives request
    ↓
Extracts JWT from header
    ↓
Verifies signature (matches secret key?)
    ↓
Checks expiry (not expired?)
    ↓
Decodes to get: user_id=5, role="admin"
    ↓
Checks: Does admin role have permission? YES
    ↓
Executes query
    ↓
audit_logger logs: "Admin 5 accessed /tickets - SUCCESS"
```

### 3. Unauthorized Access Attempt
```
Hacker sends: DELETE /tickets/1
Header: (no token)
    ↓
Server checks header → finds NO token
    ↓
Response: 401 Unauthorized
    ↓
audit_logger logs: "DELETE /tickets/1 attempted WITHOUT token - FAILED"
```

---

## 📊 Database: Keep It Simple

### Tables Created for This Project
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX (username)  -- ← Speeds up login queries
);

CREATE TABLE roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(20) UNIQUE NOT NULL  -- 'admin' or 'user'
);

CREATE TABLE user_roles (
    user_id INT NOT NULL,
    role_id INT NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (role_id) REFERENCES roles(id)
);
```

### Tables Reused from Assignment 1
```
tickets, members, categories, statuses, locations, etc.
→ No need to recreate! Just add indexes.
```

### Index Strategy
```
Index on users.username
   Why? Login query: "SELECT * FROM users WHERE username='john'"
   Without index: Search ALL users (slow)
   With index: Direct lookup (fast)

Index on tickets.user_id
   Why? Get dashboard: "SELECT * FROM tickets WHERE user_id=5"
   Without index: Search ALL tickets (slow)
   With index: Find all tickets for user 5 instantly (fast)
```

---

## 🎛️ RBAC: Role-Based Access Control Made Simple

### How It Works

```python
# In your code, decorators handle everything:

@app.route('/tickets/<id>', methods=['DELETE'])
@admin_required  # ← Only admins can reach this line
def delete_ticket(id):
    # Only admins see this code
    delete_from_db(id)
    return "Deleted"

@app.route('/mytickets', methods=['GET'])
@login_required  # ← Any logged-in user can reach this
def get_my_tickets():
    # Any user (admin or regular) sees this code
    user_id = get_current_user_id()
    return get_tickets_for_user(user_id)
```

### The Two Roles

| Action | Regular User | Admin |
|--------|--------------|-------|
| View own tickets | ✅ YES | ✅ YES |
| Create ticket | ✅ YES | ✅ YES |
| Edit own ticket | ✅ YES | ✅ YES |
| Delete own ticket | ❌ NO | ✅ YES (anyone's) |
| View other's tickets | ❌ NO | ✅ YES |
| Manage users | ❌ NO | ✅ YES |

---

## 📝 Logging: Audit Trail Everything

### What Gets Logged
```
Every API request → logs/audit.log

Format: [2024-03-18 14:32:45] USER_5 | POST /login | SUCCESS | Logged in
        [2024-03-18 14:32:50] USER_5 | GET /tickets | SUCCESS | Retrieved 3 tickets
        [2024-03-18 14:33:12] USER_5 | DELETE /tickets/2 | FAILED | Insufficient permissions
        [2024-03-18 14:35:20] UNKNOWN | GET /admin | FAILED | No valid JWT provided
```

### Why Log Everything?
1. **Security**: Detect unauthorized attempts
2. **Auditing**: Track who did what when
3. **Debugging**: See what went wrong

### Example: Catching a Hacker
```
audit.log shows:
[...] UNKNOWN | DELETE /users/1 | FAILED | Invalid JWT
[...] UNKNOWN | DELETE /users/1 | FAILED | Invalid JWT
[...] UNKNOWN | DELETE /users/1 | FAILED | Invalid JWT
[...] UNKNOWN | DELETE /users/1 | FAILED | Invalid JWT

→ Someone is attempting repeated unauthorized actions!
→ Alert admin, block IP, etc.
```

---

## ⚡ Performance: The Index Magic

### Before Indexes
```
Query: "Find all tickets for user 5" (1 million tickets in DB)

Process:
1. Load ticket 1 → is user_id = 5? No
2. Load ticket 2 → is user_id = 5? No
3. Load ticket 3 → is user_id = 5? No
... (repeat 1 million times) ...
1000000. Load ticket 1000000 → is user_id = 5? Yes!

Time: ~250ms (slow, user sees loading spinner)
```

### After Indexes
```
Query: "Find all tickets for user 5" (1 million tickets in DB)

Process:
Database uses index tree structure:
- User_5 (at index) → Points directly to tickets 12, 156, 3892, 5001

Time: ~5ms (fast, instant display)

Improvement: 50x faster!
```

---

## 🚀 Implementation Flow (Actually Building It)

### Step 1: Database Foundation
1. Create MySQL tables (users, roles, user_roles)
2. Add indexes
3. Insert sample users (admin/admin123, user/user123)

### Step 2: Backend Core
1. Create database.py (MySQL connection)
2. Create auth.py (JWT token logic)
3. Create rbac.py (permission checks)

### Step 3: API Endpoints
1. POST /login → Authenticate user
2. GET /isAuth → Check if token valid
3. GET /tickets → Get user's tickets (with permission check)
4. POST /tickets → Create new ticket
5. PUT /tickets/<id> → Update ticket (admin only)
6. DELETE /tickets/<id> → Delete ticket (admin only)

### Step 4: Frontend UI
1. login.html → Form for username/password
2. dashboard.html → Show tickets
3. admin.html → Manage users

### Step 5: Testing & Documentation
1. Run tests (try login, unauthorized access, etc.)
2. Verify audit.log
3. Benchmark performance (with/without indexes)
4. Write report

---

## 💻 Running It All Together

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Setup Database
```bash
mysql -u root -p < sql/create_tables.sql
mysql -u root -p < sql/insert_sample_data.sql
mysql -u root -p < sql/create_indexes.sql
```

### Step 3: Start Server
```bash
python run.py
```

Server now running at: http://127.0.0.1:5000

### Step 4: Use the App
1. Open browser → http://127.0.0.1:5000
2. Login with: username=`admin`, password=`admin123`
3. See dashboard with tickets
4. Try creating, updating, deleting
5. Check logs/audit.log to see all actions

---

## ✅ Final Checklist: What You Get

- ✅ Working web app with login
- ✅ Secure JWT authentication
- ✅ Role-based permissions
- ✅ Audit logging
- ✅ Database with proper indexes
- ✅ 7 API endpoints fully functional
- ✅ Simple HTML/CSS frontend
- ✅ Performance report
- ✅ ~1200 lines of readable code
- ✅ Meets ALL assignment requirements

---

## 🎓 Learning Outcomes

After completing this, you'll understand:
1. How web apps authenticate users (JWT)
2. How permissions work (RBAC)
3. How database indexing improves performance
4. How logging helps with security
5. How frontend and backend talk (REST APIs)
6. How to keep code simple and maintainable

---

## 📞 Need Help?

Each file has comments explaining:
- What function does
- What inputs it expects
- What it returns
- Why it exists

Read the comments in the code, run the app, test it, and everything makes sense!

