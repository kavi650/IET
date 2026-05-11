"""
testing_app/auth.py
Token-based access control for the testing software.
Every protected route calls require_token() to verify the bearer token.
"""
import urllib.request
import json
from functools import wraps
from flask import request, jsonify, current_app, g


def _verify_token_against_main_app(token: str) -> dict | None:
    """
    Call main app /api/access/verify/<token>.
    Returns user dict on success, None on failure.
    """
    url = f"{current_app.config['MAIN_APP_URL']}/api/access/verify/{token}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data.get('valid'):
                return data
    except Exception:
        pass
    return None


def require_token(f):
    """
    Decorator: extracts Bearer token from Authorization header,
    verifies it, and injects user info into flask.g.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401

        token = auth_header.split(' ', 1)[1].strip()
        user  = _verify_token_against_main_app(token)

        if not user:
            return jsonify({'error': 'Invalid or expired access token'}), 401

        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def get_operator_name() -> str:
    """Helper: returns the operator name from the verified token."""
    user = getattr(g, 'current_user', {})
    return user.get('full_name', 'Unknown Operator')
