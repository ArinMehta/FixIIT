# Module B: FixIIT Web Application - Implementation Plan

## 🎯 Overview
Build a simple Flask-based web application with REST APIs, RBAC, and database optimization for the FixIIT campus maintenance system.

---

## 📁 Directory Structure (Module B)

```
Module_B/
├── app/
│   ├── __init__.py              # Flask app initialization
│   ├── main.py                  # Main Flask application
│   ├── api.py                   # REST API endpoints
│   ├── auth.py                  # Authentication & JWT logic
│   ├── rbac.py                  # Role-based access control
│   ├── database.py              # Database connection & queries
│   ├── models.py                # Database models/schema
│   └── templates/
│       ├── base.html            # Base template
│       ├── login.html           # Login page
│       ├── dashboard.html       # User dashboard
│       └── admin.html           # Admin panel
├── sql/
│   ├── create_tables.sql        # Create core & project tables
│   ├── insert_sample_data.sql   # Sample users & data
│   └── create_indexes.sql       # Indexing strategy
├── logs/
│   └── audit.log                # Security audit log (auto-generated)
├── tests/
│   └── performance_test.py      # Performance benchmarking
├── config.py                    # Configuration (DB credentials, JWT secret)
├── requirements.txt             # Python dependencies
├── run.py                       # Entry point to start server
└── IMPLEMENTATION_REPORT.md     # Optimization & performance report
```

---

## 📋 Files to Create & Their Purpose

### **1. Core Application Files**

| File | Purpose | Complexity |
|------|---------|-----------|
| `app/__init__.py` | Flask app factory | Very Simple |
| `main.py` | Main Flask app with routes | Simple |
| `api.py` | REST API endpoints (login, isAuth, etc.) | Simple |
| `auth.py` | JWT token generation/validation | Simple |
| `rbac.py` | Role decorators (admin_required, user_required) | Very Simple |
| `database.py` | MySQL connection & query execution | Simple |
| `models.py` | User model, Role model | Very Simple |

### **2. Frontend Files**

| File | Purpose | Complexity |
|------|---------|-----------|
| `login.html` | Login form (username/password) | Very Simple |
| `dashboard.html` | User dashboard showing tickets | Simple |
| `admin.html` | Admin panel for managing users | Simple |
| `base.html` | Base HTML template (header, nav) | Very Simple |

### **3. Database Files**

| File | Purpose | Complexity |
|------|---------|-----------|
| `create_tables.sql` | Create local core tables (users, roles) | Simple |
| `create_indexes.sql` | Define indexes for optimization | Very Simple |
| `insert_sample_data.sql` | Add test users | Very Simple |

### **4. Supporting Files**

| File | Purpose | Complexity |
|------|---------|-----------|
| `config.py` | DB credentials, JWT secret, constants | Very Simple |
| `requirements.txt` | Python packages (Flask, PyJWT, mysql-connector) | Very Simple |
| `run.py` | Script to start Flask server | Very Simple |
| `performance_test.py` | Benchmark indexes vs no indexes | Simple |

---

## 🛠️ Implementation Approach (Step by Step)

### **Phase 1: Setup & Configuration**
1. Create `config.py` with database credentials
2. Create `requirements.txt` with: Flask, PyJWT, mysql-connector-python
3. Create `run.py` entry point

### **Phase 2: Database Layer**
1. Create `database.py` for MySQL connection
2. Create `models.py` with User and Role classes
3. Create SQL files in `sql/` folder:
   - `create_tables.sql` (create users, roles, sessions tables)
   - `insert_sample_data.sql` (add admin & regular user)
   - `create_indexes.sql` (index user_id, email columns)

### **Phase 3: Authentication & RBAC**
1. Create `auth.py`:
   - `generate_token(user_id, role)` → Returns JWT token
   - `verify_token(token)` → Validates JWT & returns user data
   - `hash_password()` → Simple hash function
   
2. Create `rbac.py`:
   - `@admin_required` decorator
   - `@login_required` decorator
   - `check_role(required_role)` function

### **Phase 4: API Endpoints**
1. Create `api.py` with Flask routes:
   - `POST /login` → Authenticate & return JWT
   - `GET /isAuth` → Validate session
   - `GET /` → Simple welcome endpoint
   - `GET /tickets` → Fetch user's tickets (login_required)
   - `POST /tickets` → Create new ticket (login_required)
   - `PUT /tickets/<id>` → Update ticket (admin_required)
   - `DELETE /tickets/<id>` → Delete ticket (admin_required)

2. Create `audit_logger.py`:
   - Log to `logs/audit.log`
   - Log session validations & unauthorized attempts

### **Phase 5: Frontend**
1. Create simple HTML templates:
   - `login.html` - Form with username/password
   - `dashboard.html` - Show tickets in table
   - `admin.html` - User management panel

2. Minimal JavaScript for:
   - Login form submission
   - Store JWT in localStorage
   - Attach token to API requests

### **Phase 6: Performance & Optimization**
1. Create `performance_test.py`:
   - Test query times WITHOUT indexes
   - Test query times WITH indexes
   - Show improvement (before/after)

2. Create `IMPLEMENTATION_REPORT.md`:
   - Explain schema design (no duplication)
   - Explain security (session validation, RBAC)
   - List indexed columns & why
   - Show performance benchmark results

---

## 🔑 Key Design Decisions (Keeping It Simple)

### **1. Database Design**
- **No Duplication**: Use existing FixIIT schema from Assignment 1
- **Minimal Core Tables**: Only add `users`, `roles`, `sessions` tables
- **Foreign Keys**: Link users to roles (RBAC)

### **2. Authentication**
- **JWT Tokens**: Simple, stateless session management
- **No Database Sessions**: Tokens contain user_id & role (decode to verify)
- **Token Expiry**: 24 hours (simple expiry logic)

### **3. RBAC Implementation**
```
Roles:
- Admin: Can create, read, update, delete tickets for all users
- Regular User: Can only view/modify their own tickets
```

### **4. Logging**
- **Audit Log**: Log every API call with:
  - Timestamp
  - User ID
  - Action (GET, POST, etc.)
  - Endpoint
  - Result (success/failure)
  - Reason for failure (invalid token, insufficient permissions)

### **5. Indexing Strategy**
- **Index on**: `users.email`, `users.id`, `tickets.user_id`, `tickets.status_id`
- **Why**: These are frequently used in WHERE clauses and JOINs

### **6. Frontend**
- **No Frontend Framework**: Just HTML/CSS/JavaScript
- **Store JWT**: Use `localStorage`
- **API Calls**: Use `fetch()` API

---

## 📊 How Everything Connects

```
User Browser
    ↓
Login.html (submit username/password)
    ↓
POST /login (api.py)
    ↓
database.py (verify user in MySQL)
    ↓
auth.py (generate JWT token)
    ↓
audit_logger.py (log successful login)
    ↓
Return JWT to browser
    ↓
Browser stores JWT in localStorage
    ↓
User accesses GET /tickets
    ↓
API checks JWT (auth.py)
    ↓
rbac.py checks if user has permission
    ↓
database.py fetches tickets from MySQL
    ↓
audit_logger.py logs the request
    ↓
Return data to dashboard.html
```

---

## ✅ Requirements Coverage

| Requirement | How We Meet It |
|-------------|----------------|
| Web UI | HTML templates (login, dashboard, admin) |
| REST APIs | Flask routes in api.py |
| Local Database | MySQL with core tables (users, roles, sessions) |
| Authentication | JWT tokens in auth.py |
| Session Validation | verify_token() in auth.py |
| RBAC | Decorators in rbac.py (@admin_required, @login_required) |
| Audit Logging | audit_logger.py logs to logs/audit.log |
| Data Integrity | Foreign keys in SQL, no data duplication |
| Indexing | create_indexes.sql creates indexes on key columns |
| Performance Benchmark | performance_test.py compares before/after |
| Report | IMPLEMENTATION_REPORT.md explains everything |

---

## 🚀 Implementation Timeline

1. **Day 1**: Setup (config, requirements, structure)
2. **Day 2**: Database layer (tables, indexes, sample data)
3. **Day 3**: Auth & RBAC (JWT, decorators)
4. **Day 4**: API endpoints (5-6 routes)
5. **Day 5**: Frontend (3 HTML templates + JavaScript)
6. **Day 6**: Logging & optimization
7. **Day 7**: Performance testing & report writing
8. **Day 8**: Video demo & final submission

---

## 💡 Why This Approach Works

✅ **Simple**: No complex ORMs, frameworks, or abstractions
✅ **Complete**: Covers all requirements
✅ **Readable**: Easy to understand and explain
✅ **Minimal**: Only necessary code, no bloat
✅ **Testable**: Can easily test each component
✅ **Scalable**: Can add features later if needed
