"""
Configuration file for FixIIT Web Application.
"""
from datetime import timedelta
import os

from dotenv import load_dotenv

load_dotenv()


def _db_config_from_env(prefix, default_port, default_database):
    """Build one MySQL config block from environment variables."""
    return {
        "host": os.getenv(f"{prefix}HOST", "localhost"),
        "user": os.getenv(f"{prefix}USER", "root"),
        "password": os.getenv(f"{prefix}PASSWORD", ""),
        "database": os.getenv(f"{prefix}NAME", default_database),
        "port": int(os.getenv(f"{prefix}PORT", str(default_port))),
        "autocommit": True,
        "use_unicode": True,
        "charset": "utf8mb4",
    }


# Flask Configuration
DEBUG = True
SECRET_KEY = "your-secret-key-change-in-production"
SESSION_TIMEOUT = timedelta(hours=24)

# Database Configuration
COORDINATOR_DB_CONFIG = _db_config_from_env("DB_", 3306, "fixiit_db")
DB_CONFIG = COORDINATOR_DB_CONFIG

TICKET_SHARD_CONFIGS = {
    0: _db_config_from_env("TICKET_SHARD_0_DB_", 3307, "fixiit_ticket_shard_0"),
    1: _db_config_from_env("TICKET_SHARD_1_DB_", 3308, "fixiit_ticket_shard_1"),
    2: _db_config_from_env("TICKET_SHARD_2_DB_", 3309, "fixiit_ticket_shard_2"),
}

LEGACY_TICKET_SOURCE_DB_CONFIG = {
    **COORDINATOR_DB_CONFIG,
    "host": os.getenv("LEGACY_TICKET_SOURCE_DB_HOST", COORDINATOR_DB_CONFIG["host"]),
    "user": os.getenv("LEGACY_TICKET_SOURCE_DB_USER", COORDINATOR_DB_CONFIG["user"]),
    "password": os.getenv("LEGACY_TICKET_SOURCE_DB_PASSWORD", COORDINATOR_DB_CONFIG["password"]),
    "database": os.getenv("LEGACY_TICKET_SOURCE_DB_NAME", COORDINATOR_DB_CONFIG["database"]),
    "port": int(
        os.getenv("LEGACY_TICKET_SOURCE_DB_PORT", str(COORDINATOR_DB_CONFIG["port"]))
    ),
}

CANONICAL_SHARD_PORTS = {
    0: 3307,
    1: 3308,
    2: 3309,
}

SOURCE_TICKET_SQL_PATH = os.getenv(
    "SOURCE_TICKET_SQL_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Track1_Assignment1_ModuleA.sql"),
)

# JWT Configuration
JWT_SECRET = "your-jwt-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

# Roles
ADMIN_ROLE = "admin"
USER_ROLE = "user"

# Application Settings
APP_NAME = "FixIIT - Campus Maintenance Management"
APP_VERSION = "1.0.0"
