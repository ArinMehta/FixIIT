"""
Configuration file for FixIIT Web Application
"""
from datetime import timedelta
import os

from dotenv import load_dotenv

load_dotenv()

# Flask Configuration
DEBUG = True
SECRET_KEY = 'your-secret-key-change-in-production'
SESSION_TIMEOUT = timedelta(hours=24)

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'fixiit_db'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'autocommit': True,
    'use_unicode': True,
    'charset': 'utf8mb4'
}

# JWT Configuration
JWT_SECRET = 'your-jwt-secret-key-change-in-production'
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = 24

# Roles
ADMIN_ROLE = 'admin'
USER_ROLE = 'user'

# Application Settings
APP_NAME = 'FixIIT - Campus Maintenance Management'
APP_VERSION = '1.0.0'
