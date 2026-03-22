"""Authentication helpers for Module B.

Uses:
- Credentials table for username/password hash
- Members table for profile data
- Member_Roles + Roles for role evaluation
"""

from datetime import datetime, timedelta, timezone

import jwt
from flask import request

from app import models
from config import JWT_ALGORITHM, JWT_EXPIRY_HOURS, JWT_SECRET


def generate_token(auth_member):
    """Create a signed JWT token for a logged-in member."""
    expires_at = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)

    payload = {
        "member_id": auth_member.member_id,
        "username": auth_member.username,
        "name": auth_member.name,
        "is_admin": auth_member.is_admin,
        "role_codes": auth_member.role_codes,
        "exp": expires_at,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token):
    """Decode and validate JWT token."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def get_bearer_token_from_request():
    """Extract bearer token from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


def validate_request_token():
    """Validate JWT from current request.

    Returns:
        (is_valid, payload_or_none, message)
    """
    token = get_bearer_token_from_request()
    if not token:
        return False, None, "Missing or malformed Authorization header"

    try:
        payload = decode_token(token)
        return True, payload, "Token is valid"
    except jwt.ExpiredSignatureError:
        return False, None, "Session expired"
    except jwt.InvalidTokenError:
        return False, None, "Invalid session token"


def login_and_issue_token(username, password):
    """Authenticate credentials and issue JWT token."""
    auth_member = models.authenticate_user(username, password)
    if not auth_member:
        return False, None, None, "Invalid credentials"

    token = generate_token(auth_member)
    return True, auth_member, token, "Login successful"
