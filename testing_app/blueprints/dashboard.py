"""testing_app/blueprints/dashboard.py — Dashboard summary API."""
from flask import Blueprint, jsonify
from sqlalchemy import func
try:
    from testing_app.extensions import db
    from testing_app.models import TestSession, TestReading, TestResult, TestSettings
    from testing_app.auth import require_token
except ImportError:
    from extensions import db
    from models import TestSession, TestReading, TestResult, TestSettings
    from auth import require_token
from datetime import datetime, date

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/tests/dashboard')


@dashboard_bp.route('', methods=['GET'])
@require_token
def summary():
    today = date.today()
    settings = TestSettings.get()

    # Active session (running)
    active = TestSession.query.filter_by(status='running').first()

    # Today's counts
    today_sessions = (TestSession.query
                      .filter(func.date(TestSession.created_at) == today)
                      .count())
    today_passed   = (TestSession.query
                      .filter(func.date(TestSession.ended_at) == today, TestSession.result == 'passed')
                      .count())
    today_failed   = (TestSession.query
                      .filter(func.date(TestSession.ended_at) == today, TestSession.result == 'failed')
                      .count())

    # All-time
    total_tests   = TestSession.query.filter_by(status='completed').count()
    total_passed  = TestSession.query.filter_by(result='passed').count()
    total_failed  = TestSession.query.filter_by(result='failed').count()
    pass_rate     = round((total_passed / total_tests * 100), 1) if total_tests else 0

    # Latest reading for active session
    latest_reading = None
    if active:
        r = (TestReading.query
             .filter_by(session_id=active.id)
             .order_by(TestReading.recorded_at.desc()).first())
        if r:
            latest_reading = r.to_dict()

    # Recent sessions
    recent = (TestSession.query
              .order_by(TestSession.created_at.desc())
              .limit(5).all())

    return jsonify({
        'machine_status':  'running' if active else 'idle',
        'active_session':  active.to_dict() if active else None,
        'latest_reading':  latest_reading,
        'today': {
            'sessions': today_sessions,
            'passed':   today_passed,
            'failed':   today_failed,
        },
        'all_time': {
            'total':     total_tests,
            'passed':    total_passed,
            'failed':    total_failed,
            'pass_rate': pass_rate,
        },
        'settings':        settings.to_dict() if settings else {},
        'recent_sessions': [s.to_dict() for s in recent],
        'timestamp':       datetime.utcnow().isoformat(),
    })
