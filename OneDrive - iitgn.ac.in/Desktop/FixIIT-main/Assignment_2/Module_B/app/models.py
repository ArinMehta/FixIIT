"""Simple model helpers for authentication-related logic.

This module intentionally avoids ORM complexity and uses explicit queries.
"""

from dataclasses import dataclass
import hashlib

from app import database


@dataclass
class AuthMember:
    """Authenticated user view for API/session usage."""

    member_id: int
    username: str
    name: str
    email: str
    contact_number: str
    address: str
    role_codes: list[str]
    is_admin: bool


def hash_password(password):
    """Hash password using SHA-256 for simple local auth usage."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password, password_hash):
    """Check plaintext password against stored SHA-256 hash."""
    return hash_password(password) == password_hash


def _parse_role_codes(role_codes_csv):
    """Convert comma-separated role codes to uppercase list."""
    if not role_codes_csv:
        return []
    return [code.strip().upper() for code in role_codes_csv.split(",") if code.strip()]


def get_auth_member_by_username(username):
    """Get joined auth+member data from Credentials and Members."""
    row = database.get_member_auth_record(username)
    if not row:
        return None

    role_codes = _parse_role_codes(row.get("role_codes"))
    return AuthMember(
        member_id=row["member_id"],
        username=row["username"],
        name=row["name"],
        email=row["email"],
        contact_number=row["contact_number"],
        address=row["address"],
        role_codes=role_codes,
        is_admin=("ADMIN" in role_codes),
    )


def authenticate_user(username, password):
    """Authenticate using Credentials + Members join and return AuthMember."""
    row = database.get_member_auth_record(username)
    if not row:
        return None

    if not verify_password(password, row["password_hash"]):
        return None

    role_codes = _parse_role_codes(row.get("role_codes"))
    return AuthMember(
        member_id=row["member_id"],
        username=row["username"],
        name=row["name"],
        email=row["email"],
        contact_number=row["contact_number"],
        address=row["address"],
        role_codes=role_codes,
        is_admin=("ADMIN" in role_codes),
    )


def create_member_credentials(member_id, username, password):
    """Create a Credentials row for an existing member_id."""
    password_hash = hash_password(password)
    return database.create_credentials(member_id, username, password_hash)


def member_is_admin(member_id):
    """Check admin status via existing Member_Roles and Roles tables."""
    return database.is_member_admin(member_id)
