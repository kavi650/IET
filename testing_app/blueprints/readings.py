"""testing_app/blueprints/readings.py — Sensor reading ingestion API."""
import random
import math
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


# ── Simulate a realistic reading ─────────────────────────────
@readings_bp.route('/sessions/<int:session_id>/simulate', methods=['POST'])
@require_token
def simulate_reading(session_id):
    """
    Generate and store a realistic simulated sensor reading.
    Called by the frontend every ~2.5s instead of Socket.IO.
    """
    session = TestSession.query.get_or_404(session_id)
    if session.status != 'running':
        return jsonify({'error': 'Session is not running'}), 409

    try:
        settings = TestSettings.get()
        p_warn = float(settings.max_pressure_bar or 250) * (settings.pressure_warning_pct or 85) / 100
        p_crit = float(settings.max_pressure_bar or 250)
        t_warn = float(settings.temp_warning_c or 65)
        t_crit = float(settings.max_temp_c or 80)
        l_warn = float(settings.leakage_warning_ml or 2)
        l_crit = float(settings.max_leakage_ml_min or 5)
    except Exception:
        db.session.rollback()
        p_warn, p_crit = 212.5, 250.0
        t_warn, t_crit = 65.0,  80.0
        l_warn, l_crit = 2.0,   5.0

    target_p = float(session.target_pressure or 150)

    # Get last reading for continuity
    last = (TestReading.query
            .filter_by(session_id=session_id)
            .order_by(TestReading.id.desc())
            .first())

    # Count existing readings to determine ramp phase
    count = TestReading.query.filter_by(session_id=session_id).count()

    # ── Pressure: ramp up over ~30 readings, then hold near target ──
    if last and last.pressure_bar is not None:
        prev_p = float(last.pressure_bar)
        if prev_p < target_p * 0.95:
            # Ramp phase: increase by 4-8 bar per reading
            pressure = min(prev_p + random.uniform(4.0, 8.0), target_p)
        else:
            # Hold phase: fluctuate ±3% around target
            pressure = target_p + random.uniform(-target_p * 0.03, target_p * 0.03)
    else:
        pressure = random.uniform(5.0, 15.0)  # first reading

    pressure = max(0.0, round(pressure, 2))

    # ── Temperature: starts at 25°C, slowly rises to 40-55°C ──
    if last and last.temperature_c is not None:
        prev_t = float(last.temperature_c)
        if prev_t < 45.0:
            temp = prev_t + random.uniform(0.3, 0.8)
        else:
            temp = prev_t + random.uniform(-0.2, 0.3)
    else:
        temp = 25.0 + random.uniform(0, 1.0)

    temp = round(temp, 2)

    # ── Flow rate: proportional to pressure + noise ──
    flow = round((pressure / target_p) * 18.0 + random.uniform(-0.5, 0.5), 3)
    flow = max(0.0, flow)

    # ── Leakage: normally near-zero, rare spikes ──
    if random.random() < 0.05:  # 5% chance of a leak spike
        leakage = round(random.uniform(0.5, 2.5), 3)
    else:
        leakage = round(random.uniform(0.0, 0.08), 3)



    reading = TestReading(
        session_id     = session_id,
        recorded_at    = datetime.utcnow(),
        pressure_bar   = pressure,
        temperature_c  = temp,
        flow_rate_lpm  = flow,
        leakage_ml_min = leakage,
        rpm            = round(random.uniform(1400, 1500), 1),
        pressure_alert = _alert_level(pressure, p_warn, p_crit),
        temp_alert     = _alert_level(temp, t_warn, t_crit),
        leakage_alert  = _alert_level(leakage, l_warn, l_crit),
    )

    try:
        db.session.add(reading)
        db.session.commit()
        return jsonify({'success': True, 'reading': reading.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



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
