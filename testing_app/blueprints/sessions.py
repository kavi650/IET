"""testing_app/blueprints/sessions.py — Test session lifecycle API."""
import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request
from testing_app.extensions import db
from testing_app.models import TestSession, TestSettings
from testing_app.auth import require_token, get_operator_name

sessions_bp = Blueprint('sessions', __name__, url_prefix='/api/tests/sessions')


def _next_session_code():
    year = datetime.utcnow().year
    count = TestSession.query.count() + 1
    return f'TS-{year}-{count:04d}'


def _check_alerts(reading_data: dict, settings: TestSettings) -> dict:
    """Return alert levels based on current settings."""
    alerts = {'pressure_alert': 'ok', 'temp_alert': 'ok', 'leakage_alert': 'ok'}
    if not settings:
        return alerts

    pressure = reading_data.get('pressure_bar', 0) or 0
    temp     = reading_data.get('temperature_c', 0) or 0
    leakage  = reading_data.get('leakage_ml_min', 0) or 0

    max_p = float(settings.max_pressure_bar or 250)
    warn_pct = (settings.pressure_warning_pct or 85) / 100
    if pressure >= max_p:
        alerts['pressure_alert'] = 'critical'
    elif pressure >= max_p * warn_pct:
        alerts['pressure_alert'] = 'warning'

    max_t = float(settings.max_temp_c or 80)
    warn_t = float(settings.temp_warning_c or 65)
    if temp >= max_t:
        alerts['temp_alert'] = 'critical'
    elif temp >= warn_t:
        alerts['temp_alert'] = 'warning'

    max_l = float(settings.max_leakage_ml_min or 5)
    warn_l = float(settings.leakage_warning_ml or 2)
    if leakage >= max_l:
        alerts['leakage_alert'] = 'critical'
    elif leakage >= warn_l:
        alerts['leakage_alert'] = 'warning'

    return alerts


# ── List sessions ────────────────────────────────────────────

@sessions_bp.route('', methods=['GET'])
@require_token
def list_sessions():
    status   = request.args.get('status')
    result   = request.args.get('result')
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    q = TestSession.query
    if status:
        q = q.filter_by(status=status)
    if result:
        q = q.filter_by(result=result)

    pg = q.order_by(TestSession.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        'sessions': [s.to_dict() for s in pg.items],
        'total': pg.total, 'pages': pg.pages, 'page': page,
    })


# ── Create session ───────────────────────────────────────────

@sessions_bp.route('', methods=['POST'])
@require_token
def create_session():
    data = request.get_json() or {}
    session = TestSession(
        session_code    = _next_session_code(),
        operator_name   = get_operator_name(),
        operator_email  = getattr(__import__('flask').g, 'current_user', {}).get('email'),
        valve_id        = data.get('valve_id'),
        valve_type      = data.get('valve_type'),
        valve_size      = data.get('valve_size'),
        client_name     = data.get('client_name'),
        job_number      = data.get('job_number'),
        test_type       = data.get('test_type', 'standard'),
        medium          = data.get('medium', 'water'),
        target_pressure = data.get('target_pressure'),
        target_duration = data.get('target_duration'),
        temperature_limit=data.get('temperature_limit'),
        notes           = data.get('notes'),
    )
    try:
        db.session.add(session)
        db.session.commit()
        return jsonify({'success': True, 'session': session.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ── Get single session ───────────────────────────────────────

@sessions_bp.route('/<int:session_id>', methods=['GET'])
@require_token
def get_session(session_id):
    s = TestSession.query.get_or_404(session_id)
    data = s.to_dict()
    if s.result_record:
        data['result_detail'] = s.result_record.to_dict()
    return jsonify(data)


# ── Start session ────────────────────────────────────────────

@sessions_bp.route('/<int:session_id>/start', methods=['PUT'])
@require_token
def start_session(session_id):
    s = TestSession.query.get_or_404(session_id)
    if s.status not in ('setup', 'paused'):
        return jsonify({'error': f'Cannot start a session with status "{s.status}"'}), 409
    s.status     = 'running'
    s.started_at = s.started_at or datetime.utcnow()
    try:
        db.session.commit()
        return jsonify({'success': True, 'session': s.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ── Pause session ────────────────────────────────────────────

@sessions_bp.route('/<int:session_id>/pause', methods=['PUT'])
@require_token
def pause_session(session_id):
    s = TestSession.query.get_or_404(session_id)
    if s.status != 'running':
        return jsonify({'error': 'Session is not running'}), 409
    s.status = 'paused'
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ── Complete session ──────────────────────────────────────────

@sessions_bp.route('/<int:session_id>/complete', methods=['PUT'])
@require_token
def complete_session(session_id):
    s    = TestSession.query.get_or_404(session_id)
    data = request.get_json() or {}

    if s.status not in ('running', 'paused'):
        return jsonify({'error': f'Cannot complete a session with status "{s.status}"'}), 409

    s.status   = 'completed'
    s.ended_at = datetime.utcnow()
    if s.started_at:
        s.duration_seconds = int((s.ended_at - s.started_at).total_seconds())
    s.result      = data.get('result', 'passed')
    s.reviewed_by = get_operator_name()
    s.notes       = data.get('notes', s.notes)

    try:
        # Auto-generate result summary
        _generate_result_summary(s)
        db.session.commit()
        # Emit SocketIO event
        try:
            from testing_app.app import socketio
            socketio.emit('session_completed', {'session_id': s.id, 'result': s.result})
        except Exception:
            pass
        return jsonify({'success': True, 'session': s.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ── Abort session ────────────────────────────────────────────

@sessions_bp.route('/<int:session_id>/abort', methods=['PUT'])
@require_token
def abort_session(session_id):
    s = TestSession.query.get_or_404(session_id)
    if s.status == 'completed':
        return jsonify({'error': 'Session already completed'}), 409
    s.status   = 'aborted'
    s.ended_at = datetime.utcnow()
    s.result   = 'inconclusive'
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ── Internal: build result summary row ──────────────────────

def _generate_result_summary(session: TestSession):
    """Aggregate all readings for the session into TestResult."""
    from testing_app.models import TestReading, TestResult
    from sqlalchemy import func

    settings = TestSettings.get()

    stats = db.session.query(
        func.max(TestReading.pressure_bar).label('max_p'),
        func.min(TestReading.pressure_bar).label('min_p'),
        func.avg(TestReading.pressure_bar).label('avg_p'),
        func.max(TestReading.temperature_c).label('max_t'),
        func.avg(TestReading.flow_rate_lpm).label('avg_fl'),
        func.max(TestReading.leakage_ml_min).label('max_l'),
    ).filter(TestReading.session_id == session.id).one()

    max_l        = float(stats.max_l or 0)
    leakage_lim  = float(settings.max_leakage_ml_min or 5) if settings else 5
    pressure_lim = float(settings.max_pressure_bar or 250) if settings else 250
    max_t        = float(stats.max_t or 0)
    temp_lim     = float(settings.max_temp_c or 80) if settings else 80

    result = session.result_record
    if not result:
        result = TestResult(session_id=session.id)
        db.session.add(result)

    result.max_pressure_bar      = stats.max_p
    result.min_pressure_bar      = stats.min_p
    result.avg_pressure_bar      = stats.avg_p
    result.max_temperature_c     = stats.max_t
    result.avg_flow_rate_lpm     = stats.avg_fl
    result.max_leakage_ml_min    = stats.max_l
    result.pressure_hold_ok      = session.result == 'passed'
    result.leakage_within_limit  = max_l <= leakage_lim
    result.temperature_ok        = max_t <= temp_lim
    result.pressure_limit_bar    = pressure_lim
    result.leakage_limit_ml_min  = leakage_lim
    result.duration_achieved_sec = session.duration_seconds
    result.engineer_signed_by    = session.reviewed_by
