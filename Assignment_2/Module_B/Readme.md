# FixIIT Module B - Campus Maintenance System

A Flask-based web application for managing campus maintenance requests with role-based access control (RBAC), audit logging, and ticket management.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Database Setup](#database-setup)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Demo Credentials](#demo-credentials)
- [Important Notes Before Running](#important-notes-before-running)

---

## Prerequisites

- **Python**: 3.8 or higher
- **MySQL**: 5.7 or higher (or compatible version)
- **pip**: Python package installer

Verify installed versions:
```bash
python --version
python3 --version
mysql --version
```

---

## Installation

### 1. Create and Activate Virtual Environment

```bash
# Navigate to Module_B directory
cd /Users/sohamshrivastava/Desktop/Database_project/FixIIT/Module_B

# Create virtual environment
python3 -m venv myenv

# Activate virtual environment (macOS/Linux)
source myenv/bin/activate

# Activate virtual environment (Windows)
myenv\Scripts\activate
```

### 2. Install Python Dependencies

```bash
# Install from requirements.txt
pip install -r requirements.txt

# Or manually install key packages
pip install flask==2.3.3
pip install pyjwt==2.8.1
pip install mysql-connector-python==8.0.33
python-dotenv==1.0.0
```

---

## Database Setup

### 1. Start MySQL Service

Start your MySQL server

### 2. Verify MySQL Connection

Test your MySQL connection with the credentials you'll use in `.env`:

```bash
# Test connection to your MySQL server
mysql -h 127.0.0.1 -u root -p -e "SELECT 1;"
```

If this fails, ensure MySQL is running on your system before proceeding.

### 3. Set Up Environment Configuration

Create `.env` file in Module_B directory (copy from `.env_demo` if needed):

```bash
# Copy demo config
cp .env_demo .env

# Edit .env with your MySQL credentials
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=fixiit_db
```

### 4. Create Database and Tables

**Option A: Run all SQL files in order**

```bash
# Navigate to Module_B SQL directory
cd /Users/sohamshrivastava/Desktop/Database_project/FixIIT

# Import main FixIIT schema (Module A)
mysql -h 127.0.0.1 -u root -p"your_mysql_password" < Track1_Assignment1_ModuleA.sql

# Import Module B specific tables
cd Module_B
mysql -h 127.0.0.1 -u root -p"your_mysql_password" < sql/create_tables.sql

# Insert sample data
mysql -h 127.0.0.1 -u root -p"your_mysql_password" < sql/insert_sample_data.sql

# (Optional) Create indexes for performance
mysql -h 127.0.0.1 -u root -p"your_mysql_password" < sql/create_indexes.sql
```

**Option B: Verify database is set up**

```bash
# Check if database exists
mysql -h 127.0.0.1 -u root -p"your_mysql_password" -e "SHOW DATABASES;"

# Check tables in fixiit_db
mysql -h 127.0.0.1 -u root -p"your_mysql_password" -e "USE fixiit_db; SHOW TABLES;"
```

### 5. Verify Database Setup

If you encounter any issues, check your MySQL:

```bash
# Verify database exists
mysql -h 127.0.0.1 -u root -p -e "SHOW DATABASES;"

# Check all required tables are present
mysql -h 127.0.0.1 -u root -p -e "USE fixiit_db; SHOW TABLES;"

# Verify sample data (credentials) exist
mysql -h 127.0.0.1 -u root -p -e "USE fixiit_db; SELECT * FROM Credentials;"
```

**Ensure:**
- MySQL service is running on your system
- Database `fixiit_db` exists with all tables
- Sample data has been inserted (demo users available)
- `.env` file contains correct MySQL credentials

---

## Configuration

### Environment Variables (.env)

```bash
# Database connection
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_secure_password
DB_NAME=fixiit_db

# Flask app settings (optional, defaults are in config.py)
APP_PORT=5000
```

### Flask Configuration (config.py)

Key settings:
- `DEBUG = True` (development mode, auto-reload)
- `SECRET_KEY` = Your Flask secret (change in production)
- `JWT_SECRET` = Your JWT signing secret (change in production)
- `JWT_EXPIRY_HOURS = 24` (token expiration)

---

## Running the Application

### 1. Activate Virtual Environment

```bash
cd /Users/sohamshrivastava/Desktop/Database_project/FixIIT/Module_B
source myenv/bin/activate  # macOS/Linux
# or
myenv\Scripts\activate     # Windows
```

### 2. Start Flask Development Server

```bash
# Basic run
python run.py

# With specific port
python run.py --port 5001

# With environment variables
export FLASK_ENV=development
export FLASK_DEBUG=1
python run.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
 * Debugger PIN: XXX-XXX-XXX
```

### 3. Access the Application

- **Login Page**: http://127.0.0.1:5000/login
- **Dashboard**: http://127.0.0.1:5000/dashboard (after login)
- **Profile**: http://127.0.0.1:5000/portfolio (after login)
- **Admin Panel**: http://127.0.0.1:5000/admin (admin users only)

### 4. Stop the Server

```bash
# Press CTRL+C in terminal
```

---

## API Endpoints

### Authentication

**Login (POST)**
```bash
curl -X POST http://127.0.0.1:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**Check Auth Status (GET)**
```bash
curl -X GET http://127.0.0.1:5000/isAuth \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Portfolio/Profile Management

**Get Profile (GET)**
```bash
curl -X GET http://127.0.0.1:5000/portfolio/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Update Profile (PUT)**
```bash
curl -X PUT http://127.0.0.1:5000/portfolio/me \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "name":"John Doe",
    "email":"john@example.com",
    "contact_number":"1234567890",
    "address":"City, State",
    "bio":"My bio here",
    "skills":"skill1,skill2",
    "github_url":"https://github.com/username",
    "linkedin_url":"https://linkedin.com/in/username",
    "current_password":"oldpass123",
    "new_password":"newpass123"
  }'
```

### Tickets

**Get All User Tickets (GET)**
```bash
curl -X GET http://127.0.0.1:5000/tickets \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Create Ticket (POST)**
```bash
curl -X POST http://127.0.0.1:5000/tickets \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "location_id":1,
    "category_id":2,
    "description":"Issue description here"
  }'
```

**Get All Tickets (Admin) (GET)**
```bash
curl -X GET http://127.0.0.1:5000/admin/tickets \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Demo Credentials

### User Account (Regular Member)
- **Username**: `user`
- **Password**: `user123`
- **Member ID**: 2

### Admin Account (Administrator)
- **Username**: `admin`
- **Password**: `admin123`
- **Member ID**: 28

**Test Login:**
```bash
curl -X POST http://127.0.0.1:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"user123"}'
```

---

## Important Notes Before Running

### ✅ Prerequisites Checklist

1. **MySQL Service Running**
   - Ensure MySQL is started and running on your system
   - Verify it's accessible at `localhost:3306`
   - If you encounter connection issues, check your MySQL installation

2. **Database Schema Exists**
   - The database `fixiit_db` should already be created from running the SQL files
   - All required tables should be present (members, tickets, categories, locations, roles, Credentials, member_portfolio, etc.)
   - Verify by running:
     ```bash
     mysql -h 127.0.0.1 -u root -p -e "USE fixiit_db; SHOW TABLES;"
     ```

3. **Environment File (.env) Created**
   - Create `.env` file in Module_B directory with your MySQL password:
     ```bash
     DB_HOST=localhost
     DB_PORT=3306
     DB_USER=root
     DB_PASSWORD=your_actual_mysql_password
     DB_NAME=fixiit_db
     ```
   - **Never commit .env to version control** - it contains sensitive credentials
   - The app will read credentials from this file on startup

4. **Sample Data Inserted**
   - Demo user credentials should be in the `Credentials` table:
     - Username: `user`, Password: `user123` (member_id: 2)
     - Username: `admin`, Password: `admin123` (member_id: 28)
   - Verify with: `mysql -h 127.0.0.1 -u root -p -e "USE fixiit_db; SELECT * FROM Credentials;"`

---

## Project Structure

```
Module_B/
├── app/                      # Flask application
│   ├── __init__.py          # App factory
│   ├── api.py               # API routes
│   ├── auth.py              # JWT authentication
│   ├── database.py          # Database queries
│   ├── models.py            # Data models
│   ├── audit_logger.py      # Audit logging
│   ├── rbac.py              # Role-based access control
├── templates/               # HTML templates
│   ├── login.html
│   ├── dashboard.html
│   ├── portfolio.html
│   ├── admin.html
├── static/                  # CSS/JS assets
│   ├── style.css
├── sql/                     # Database setup scripts
│   ├── create_tables.sql
│   ├── insert_sample_data.sql
│   ├── create_indexes.sql
│   ├── create_audit_triggers.sql
├── logs/                    # Application logs
├── config.py                # Flask configuration
├── run.py                   # Entry point
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create from .env_demo)
└── README.md                # This file
```

---

## Support

For issues or questions:
1. Check the **Important Notes Before Running** section - ensure MySQL is running and schema is set up
2. Verify your `.env` file has correct MySQL credentials
3. Check that all SQL files were imported successfully
4. Review Flask/MySQL documentation
5. Check audit logs in `logs/audit.log` for application errors
