"""
blueprints/access.py
Public-facing routes for Testing Software Access Requests.
  POST /api/access/request   → submit a new request
  GET  /api/access/verify/<token> → testing app calls this to validate token
"""
import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request
from models import db
from models_v3 import TestingAccessRequest, ActivityLog, log_activity

access_bp = Blueprint('access', __name__, url_prefix='/api/access')


# ── helpers ────────────────────────────────────────────────────

def _validate_request_body(data, required):
    """Return error string or None."""
    for field in required:
        if not data.get(field, '').strip():
            return f"'{field}' is required"
    return None


# ── Submit Access Request (public, no auth) ────────────────────

@access_bp.route('/request', methods=['POST'])
def submit_request():
    """Public users submit an access request."""
    data = request.get_json() or {}
    err  = _validate_request_body(data, ['full_name', 'email', 'purpose'])
    if err:
        return jsonify({'error': err}), 400

    # Prevent duplicate pending requests from same email
    existing = TestingAccessRequest.query.filter_by(
        email=data['email'].strip().lower(), status='pending'
    ).first()
    if existing:
        return jsonify({
            'error': 'A pending request already exists for this email address.'
        }), 409

    req = TestingAccessRequest(
        full_name    = data['full_name'].strip(),
        email        = data['email'].strip().lower(),
        company_name = data.get('company_name', '').strip() or None,
        phone        = data.get('phone', '').strip() or None,
        purpose      = data['purpose'].strip(),
    )

    try:
        db.session.add(req)
        db.session.commit()
        log_activity(
            action='submitted_access_request',
            entity_type='access_request', entity_id=req.id,
            description=f"{req.full_name} <{req.email}> requested testing access",
        )
        db.session.commit()
        return jsonify({'success': True, 'message': 'Request submitted. Admin will review shortly.'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ── Token Verification (called by testing app) ─────────────────

@access_bp.route('/verify/<token>', methods=['GET'])
def verify_token(token):
    """
    Testing software calls this before granting dashboard access.
    Returns 200 + user info if valid, 401/403 if not.
    """
    req = TestingAccessRequest.query.filter_by(access_token=token).first()

    if not req:
        return jsonify({'valid': False, 'reason': 'Token not found'}), 401

    if req.status != 'approved':
        return jsonify({'valid': False, 'reason': f'Request is {req.status}'}), 403

    if req.token_expires_at and datetime.utcnow() > req.token_expires_at:
        return jsonify({'valid': False, 'reason': 'Token has expired'}), 401

    return jsonify({
        'valid':        True,
        'full_name':    req.full_name,
        'email':        req.email,
        'company_name': req.company_name,
        'request_id':   req.id,
    }), 200


# ── Check status by email (for public status page) ─────────────

@access_bp.route('/status', methods=['GET'])
def check_status():
    """Public users check their request status by email."""
    email = (request.args.get('email') or '').strip().lower()
    if not email:
        return jsonify({'error': 'email is required'}), 400

    req = TestingAccessRequest.query.filter_by(email=email).order_by(
        TestingAccessRequest.created_at.desc()
    ).first()

    if not req:
        return jsonify({'found': False}), 404

    return jsonify({
        'found':          True,
        'status':         req.status,
        'rejection_note': req.rejection_note if req.status == 'rejected' else None,
        'actioned_at':    req.actioned_at.isoformat() if req.actioned_at else None,
    }), 200
