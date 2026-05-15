"""testing_app/blueprints/readings.py — Sensor reading ingestion API."""
from datetime import datetime
from flask import Blueprint, jsonify, request
try:
    from testing_app.extensions import db
    from testing_app.models import TestSession, TestReading, TestSettings
    from testing_app.auth import require_token
except ImportError:
    from extensions import db
    from models import TestSession, TestReading, TestSettings
    from auth import require_token

readings_bp = Blueprint('readings', __name__, url_prefix='/api/tests')


def _alert_level(value, warn_threshold, critical_threshold):
    if value is None:
        return 'ok'
    if value >= critical_threshold:
        return 'critical'
    if value >= warn_threshold:
        return 'warning'
    return 'ok'


# ── Push single reading ──────────────────────────────────────

@readings_bp.route('/sessions/<int:session_id>/readings', methods=['POST'])
@require_token
def push_reading(session_id):
    session = TestSession.query.get_or_404(session_id)
    if session.status != 'running':
        return jsonify({'error': 'Session is not running'}), 409

    data     = request.get_json() or {}
    settings = TestSettings.get()

    pressure  = data.get('pressure_bar')
    temp      = data.get('temperature_c')
    leakage   = data.get('leakage_ml_min')

    # Determine alert levels
    p_warn = float(settings.max_pressure_bar or 250) * (settings.pressure_warning_pct or 85) / 100
    p_crit = float(settings.max_pressure_bar or 250)
    t_warn = float(settings.temp_warning_c or 65)
    t_crit = float(settings.max_temp_c or 80)
    l_warn = float(settings.leakage_warning_ml or 2)
    l_crit = float(settings.max_leakage_ml_min or 5)

    reading = TestReading(
        session_id     = session_id,
        recorded_at    = datetime.utcnow(),
        pressure_bar   = pressure,
        temperature_c  = temp,
        flow_rate_lpm  = data.get('flow_rate_lpm'),
        leakage_ml_min = leakage,
        rpm            = data.get('rpm'),
        pressure_alert = _alert_level(pressure, p_warn, p_crit),
        temp_alert     = _alert_level(temp, t_warn, t_crit),
        leakage_alert  = _alert_level(leakage, l_warn, l_crit),
    )

    try:
        db.session.add(reading)
        db.session.commit()

        r_dict = reading.to_dict()

        # Emit via SocketIO for live dashboard
        try:
            try:
                from testing_app.app import socketio
            except ImportError:
                from app import socketio
            if socketio:
                socketio.emit('new_reading', r_dict, room=f'session_{session_id}')
                if 'critical' in [r_dict['pressure_alert'], r_dict['temp_alert'], r_dict['leakage_alert']]:
                    socketio.emit('critical_alert', r_dict, room=f'session_{session_id}')
        except Exception:
            pass

        return jsonify({'success': True, 'reading': r_dict}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ── Push bulk readings (batch from hardware) ─────────────────

@readings_bp.route('/sessions/<int:session_id>/readings/bulk', methods=['POST'])
@require_token
def push_bulk_readings(session_id):
    session = TestSession.query.get_or_404(session_id)
    if session.status != 'running':
        return jsonify({'error': 'Session is not running'}), 409

    items    = request.get_json() or []
    settings = TestSettings.get()

    p_warn = float(settings.max_pressure_bar or 250) * (settings.pressure_warning_pct or 85) / 100
    p_crit = float(settings.max_pressure_bar or 250)
    t_warn = float(settings.temp_warning_c or 65)
    t_crit = float(settings.max_temp_c or 80)
    l_warn = float(settings.leakage_warning_ml or 2)
    l_crit = float(settings.max_leakage_ml_min or 5)

    readings = []
    for d in items:
        pressure = d.get('pressure_bar')
        temp     = d.get('temperature_c')
        leakage  = d.get('leakage_ml_min')
        readings.append(TestReading(
            session_id     = session_id,
            recorded_at    = datetime.fromisoformat(d['recorded_at']) if d.get('recorded_at') else datetime.utcnow(),
            pressure_bar   = pressure,
            temperature_c  = temp,
            flow_rate_lpm  = d.get('flow_rate_lpm'),
            leakage_ml_min = leakage,
            rpm            = d.get('rpm'),
            pressure_alert = _alert_level(pressure, p_warn, p_crit),
            temp_alert     = _alert_level(temp, t_warn, t_crit),
            leakage_alert  = _alert_level(leakage, l_warn, l_crit),
        ))

    try:
        db.session.bulk_save_objects(readings)
        db.session.commit()
        return jsonify({'success': True, 'count': len(readings)}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ── Fetch readings (for charts) ──────────────────────────────

@readings_bp.route('/sessions/<int:session_id>/readings', methods=['GET'])
@require_token
def get_readings(session_id):
    limit  = request.args.get('limit', 500, type=int)
    latest = request.args.get('latest', 0, type=int)    # get only readings after this ID

    q = TestReading.query.filter_by(session_id=session_id)
    if latest:
        q = q.filter(TestReading.id > latest)

    readings = q.order_by(TestReading.recorded_at.asc()).limit(min(limit, 5000)).all()
    return jsonify({
        'readings': [r.to_dict() for r in readings],
        'count':    len(readings),
    })


# ── Latest single reading (live status) ─────────────────────

@readings_bp.route('/sessions/<int:session_id>/readings/latest', methods=['GET'])
@require_token
def latest_reading(session_id):
    r = (TestReading.query
         .filter_by(session_id=session_id)
         .order_by(TestReading.recorded_at.desc())
         .first())
    if not r:
        return jsonify({'reading': None})
    return jsonify({'reading': r.to_dict()})
