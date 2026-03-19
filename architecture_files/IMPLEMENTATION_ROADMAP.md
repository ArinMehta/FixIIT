# Module B Implementation Roadmap
## Step-by-Step Checklist

### Phase 1: Foundation Setup ✅ (DONE)
- [x] Create directory structure
- [x] Create config.py (database credentials, JWT secret)
- [x] Create requirements.txt (Flask, PyJWT, mysql-connector)
- [x] Create run.py (entry point)

---

### Phase 2: Database Layer (NEXT - HIGH PRIORITY)

#### 2.1 Create Database Connection
- [ ] Create `app/database.py`:
  - Database connection management
  - Generic query execution function
  - Result formatting

#### 2.2 Create Database Models
- [ ] Create `app/models.py`:
  - User class
  - Role class
  - Helper functions (hash_password, verify_password)

#### 2.3 Create SQL Scripts
- [ ] Create `sql/create_tables.sql`:
  - users table (id, username, password_hash)
  - roles table (id, role_name)
  - user_roles table (user_id, role_id)
  - sessions table (optional, for audit trail)

- [ ] Create `sql/insert_sample_data.sql`:
  - Insert admin user (admin/admin123)
  - Insert regular user (user/user123)
  - Assign roles

- [ ] Create `sql/create_indexes.sql`:
  - Index on users.username
  - Index on user_roles.user_id
  - Index on tickets.user_id (from FixIIT)

---

### Phase 3: Authentication & RBAC (NEXT - HIGH PRIORITY)

#### 3.1 Create Authentication Module
- [ ] Create `app/auth.py`:
  - `generate_token(user_id, role)` function
  - `verify_token(token)` function
  - Token expiry logic

#### 3.2 Create RBAC Module
- [ ] Create `app/rbac.py`:
  - `@login_required` decorator
  - `@admin_required` decorator
  - Permission checking logic

#### 3.3 Create Logger
- [ ] Create `app/audit_logger.py`:
  - Setup logging to `logs/audit.log`
  - Log format: [TIMESTAMP] USER_ID | ACTION | ENDPOINT | STATUS | MESSAGE

---

### Phase 4: REST API Implementation (HIGH PRIORITY)

#### 4.1 Create API Module
- [ ] Create `app/api.py`:
  - Routes in api.py:
    - POST /login
    - GET /isAuth
    - GET /
    - GET /tickets (login_required)
    - POST /tickets (login_required)
    - PUT /tickets/<id> (admin_required)
    - DELETE /tickets/<id> (admin_required)

#### 4.2 Create Flask App Factory
- [ ] Create `app/__init__.py`:
  - Flask app factory function `create_app()`
  - Register blueprints
  - Error handling

#### 4.3 Create Main App
- [ ] Create `app/main.py`:
  - Initialize Flask with API routes

---

### Phase 5: Frontend Development (MEDIUM PRIORITY)

#### 5.1 Create Frontend Templates
- [ ] Create `app/templates/base.html`:
  - Base HTML template
  - Navigation bar
  - CSS styling

- [ ] Create `app/templates/login.html`:
  - Login form
  - Username/password fields
  - Submit button
  - JavaScript to call POST /login

- [ ] Create `app/templates/dashboard.html`:
  - Display user's tickets in table
  - Create new ticket form
  - Edit/delete buttons (admin only)
  - Fetch data using GET /tickets

- [ ] Create `app/templates/admin.html`:
  - User management panel
  - List all users
  - Delete users (admin only)

#### 5.2 Add Frontend Logic
- [ ] JavaScript functions:
  - Store JWT in localStorage
  - Attach JWT to API headers
  - Handle login/logout
  - Display error messages

---

### Phase 6: Performance & Optim (MEDIUM PRIORITY)

#### 6.1 Create Performance Tests
- [ ] Create `tests/performance_test.py`:
  - Test WITHOUT indexes: measure query time
  - Test WITH indexes: measure query time
  - Compare results (should show 10-50x improvement)

#### 6.2 Create Implementation Report
- [ ] Create `IMPLEMENTATION_REPORT.md`:
  - Schema design explanation
  - Security explanation
  - Indexing strategy
  - Performance benchmarks
  - Screenshots/results

---

### Phase 7: Testing & Debugging (MEDIUM PRIORITY)

- [ ] Setup MySQL database from Assignment 1
- [ ] Run `python run.py` to start Flask server
- [ ] Test /login endpoint
- [ ] Test /isAuth endpoint
- [ ] Test /tickets endpoint (with JWT)
- [ ] Test admin-only endpoints
- [ ] Verify audit.log is being written
- [ ] Test with wrong credentials (should fail + log)
- [ ] Test without JWT token (should fail + log)

---

### Phase 8: Video Demonstration (LOW PRIORITY)

- [ ] Record 3-5 minute video showing:
  - Login flow (user/password)
  - Dashboard (viewing tickets)
  - Admin panel (manage users)
  - Audit log (show logged actions)
  - RBAC in action (user can't access admin features)
- [ ] Upload to YouTube (Unlisted) or Google Drive
- [ ] Add link to IMPLEMENTATION_REPORT.md

---

## 📊 Complexity Breakdown

| Component | Complexity | Est. Lines | Priority |
|-----------|-----------|-----------|----------|
| config.py | Very Simple | ~40 | ✅ DONE |
| database.py | Simple | ~80 | ⛔ NEXT |
| models.py | Very Simple | ~60 | ⛔ NEXT |
| auth.py | Simple | ~70 | ⛔ NEXT |
| rbac.py | Very Simple | ~40 | ⛔ NEXT |
| api.py | Simple | ~150 | ⛔ NEXT |
| app/__init__.py | Very Simple | ~30 | ⛔ NEXT |
| audit_logger.py | Very Simple | ~50 | ⛔ NEXT |
| SQL files | Very Simple | ~100 | ⛔ NEXT |
| Templates (HTML) | Simple | ~200 | ⛔ NEXT |
| performance_test.py | Simple | ~100 | ⛔ LATER |
| IMPLEMENTATION_REPORT.md | Simple | ~300 | ⛔ LATER |
| **TOTAL** | | **~1220** | |

---

## 🎯 How We'll Build This

### Strategy: Bottom-Up Approach
1. Start with **database layer** (foundation)
2. Add **authentication** (security)
3. Build **API endpoints** (functionality)
4. Create **frontend** (UI)
5. Optimize and test

### Why Bottom-Up?
- Database needs to work first (everything depends on it)
- Auth needs to work before APIs (security foundation)
- APIs need to work before frontend (data source)
- Frontend last (displays the data)

---

## 💡 Key Points While Implementing

1. **Keep it simple**: Don't over-engineer anything
2. **Test as you go**: Create small pieces, test them
3. **Use existing schema**: Don't duplicate tables from Assignment 1
4. **Log everything**: Every API call should be logged
5. **Index wisely**: Only index columns used in WHERE/JOIN
6. **Comments in code**: Add comments explaining what each function does
7. **Error handling**: Clear error messages for debugging

---

## ⏱️ Expected Time per Phase

- Phase 1: **1 hour** (Setup) ✅ DONE
- Phase 2: **2 hours** (Database)
- Phase 3: **2 hours** (Auth & RBAC)
- Phase 4: **3 hours** (API)
- Phase 5: **2 hours** (Frontend)
- Phase 6: **1 hour** (Performance)
- Phase 7: **1 hour** (Testing)
- Phase 8: **1 hour** (Video)

**Total: ~13 hours** for complete Module B

---

## 📝 Notes

- All code will have comments explaining what it does
- No complex patterns, just straightforward Python
- Easy to modify if requirements change
- Can run locally with `python run.py` after setup
