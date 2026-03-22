"""Role-based access control decorators for Module B."""

from functools import wraps

from flask import g, jsonify

from app import auth, models
from app.audit_logger import log_security_event


def login_required(func):
    """Allow access only when a valid JWT is provided."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        is_valid, payload, message = auth.validate_request_token()
        if not is_valid:
            log_security_event(
                endpoint="protected_endpoint",
                status="FAILED",
                message=message,
                member_id=None,
            )
            return jsonify({"error": message}), 401

        # Store auth payload on Flask global context for downstream use.
        g.auth_payload = payload
        g.member_id = payload.get("member_id")
        g.username = payload.get("username")
        return func(*args, **kwargs)

    return wrapper


def admin_required(func):
    """Allow access only to members with ADMIN role mapping."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        is_valid, payload, message = auth.validate_request_token()
        if not is_valid:
            log_security_event(
                endpoint="admin_endpoint",
                status="FAILED",
                message=message,
                member_id=None,
            )
            return jsonify({"error": message}), 401

        member_id = payload.get("member_id")
        if not member_id:
            log_security_event(
                endpoint="admin_endpoint",
                status="FAILED",
                message="Token missing member_id",
                member_id=None,
            )
            return jsonify({"error": "Invalid session token"}), 401

        if not models.member_is_admin(member_id):
            log_security_event(
                endpoint="admin_endpoint",
                status="FAILED",
                message="Admin role required",
                member_id=member_id,
            )
            return jsonify({"error": "Admin access required"}), 403

        g.auth_payload = payload
        g.member_id = member_id
        g.username = payload.get("username")
        return func(*args, **kwargs)

    return wrapper
