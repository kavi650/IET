"""testing_app/blueprints/settings.py — Machine settings CRUD."""
from datetime import datetime
from flask import Blueprint, jsonify, request
from testing_app.extensions import db
from testing_app.models import TestSettings
from testing_app.auth import require_token

settings_bp = Blueprint('settings', __name__, url_prefix='/api/tests/settings')

EDITABLE_FIELDS = [
    'max_pressure_bar', 'min_pressure_bar', 'pressure_warning_pct',
    'max_leakage_ml_min', 'leakage_warning_ml',
    'max_temp_c', 'temp_warning_c',
    'default_duration_sec', 'reading_interval_ms',
    'ai_enabled', 'ai_model', 'ai_sensitivity',
]


@settings_bp.route('', methods=['GET'])
@require_token
def get_settings():
    s = TestSettings.get()
    if not s:
        return jsonify({'error': 'Settings not initialised. Run migrate_v3.py.'}), 500
    return jsonify(s.to_dict())


@settings_bp.route('', methods=['PUT'])
@require_token
def update_settings():
    s    = TestSettings.get()
    data = request.get_json() or {}
    for field in EDITABLE_FIELDS:
        if field in data:
            setattr(s, field, data[field])
    s.updated_at = datetime.utcnow()
    try:
        db.session.commit()
        return jsonify({'success': True, 'settings': s.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@settings_bp.route('/calibrate', methods=['PUT'])
@require_token
def log_calibration():
    s    = TestSettings.get()
    data = request.get_json() or {}
    if not data.get('calibrated_by'):
        return jsonify({'error': 'calibrated_by is required'}), 400
    s.last_calibrated_at = datetime.utcnow()
    s.calibrated_by      = data['calibrated_by']
    s.calibration_notes  = data.get('calibration_notes', '')
    s.updated_at         = datetime.utcnow()
    try:
        db.session.commit()
        return jsonify({'success': True, 'calibrated_at': s.last_calibrated_at.isoformat()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
