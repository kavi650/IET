"""
testing_app/auth.py
Token-based access control for the testing software.
Verifies tokens directly via the shared database — no HTTP cross-service calls.
"""
from functools import wraps
from datetime import datetime, timezone
from flask import request, jsonify, g


def _verify_token_db(token: str) -> dict | None:
    """
    Verify token directly against the shared PostgreSQL database.
    Much faster than HTTP — no cross-service call needed since both
    apps share the same DB.
    """
    try:
        try:
            from testing_app.extensions import db
        except ImportError:
            from extensions import db

        from sqlalchemy import text
        result = db.session.execute(
            text("""
                SELECT full_name, email, company_name, token_expires_at
                FROM access_requests
                WHERE token = :token AND status = 'approved'
                LIMIT 1
            """),
            {"token": token}
        ).fetchone()

        if not result:
            return None

        # Check expiry
        if result.token_expires_at:
            expires = result.token_expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires:
                return None

        return {
            "valid": True,
            "full_name": result.full_name,
            "email": result.email,
            "company_name": result.company_name,
        }
    except Exception:
        try:
            from testing_app.extensions import db as _db
        except ImportError:
            try:
                from extensions import db as _db
            except ImportError:
                _db = None
        if _db:
            try:
                _db.session.rollback()
            except Exception:
                pass
        # Fail-open: allow access if DB check fails
        return {"valid": True, "full_name": "Operator", "email": "", "company_name": ""}


def require_token(f):
    """
    Decorator: extracts Bearer token from Authorization header,
    verifies it against the shared DB, and injects user info into flask.g.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing Authorization header'}), 401

        token = auth_header.split(' ', 1)[1].strip()
        if not token:
            return jsonify({'error': 'Empty token'}), 401

        user = _verify_token_db(token)
        if not user:
            return jsonify({'error': 'Invalid or expired access token'}), 401

        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def get_operator_name() -> str:
    """Helper: returns the operator name from the verified token."""
    user = getattr(g, 'current_user', {})
    return user.get('full_name', 'Unknown Operator')
