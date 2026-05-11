"""testing_app/blueprints/analysis.py — Statistical analysis and chart data."""
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from testing_app.extensions import db
from testing_app.models import TestSession, TestReading, TestResult
from testing_app.auth import require_token

analysis_bp = Blueprint('analysis', __name__, url_prefix='/api/tests/analysis')


@analysis_bp.route('/session/<int:session_id>', methods=['GET'])
@require_token
def session_analysis(session_id):
    """Full analysis for one session: time-series + stats."""
    s = TestSession.query.get_or_404(session_id)

    readings = (TestReading.query
                .filter_by(session_id=session_id)
                .order_by(TestReading.recorded_at.asc()).all())

    if not readings:
        return jsonify({'session': s.to_dict(), 'readings': [], 'stats': {}})

    def _f(v): return float(v) if v is not None else None

    # Time-series lists for charts (Plotly / ApexCharts / Chart.js)
    timestamps   = [r.recorded_at.isoformat() for r in readings]
    pressures    = [_f(r.pressure_bar)   for r in readings]
    temperatures = [_f(r.temperature_c)  for r in readings]
    flows        = [_f(r.flow_rate_lpm)  for r in readings]
    leakages     = [_f(r.leakage_ml_min) for r in readings]
    rpms         = [_f(r.rpm)            for r in readings]

    # Aggregate stats
    p_vals = [x for x in pressures   if x is not None]
    t_vals = [x for x in temperatures if x is not None]
    l_vals = [x for x in leakages    if x is not None]
    f_vals = [x for x in flows       if x is not None]

    def safe_avg(lst): return round(sum(lst) / len(lst), 3) if lst else None

    stats = {
        'pressure':   {'max': max(p_vals, default=None), 'min': min(p_vals, default=None), 'avg': safe_avg(p_vals)},
        'temperature':{'max': max(t_vals, default=None), 'min': min(t_vals, default=None), 'avg': safe_avg(t_vals)},
        'leakage':    {'max': max(l_vals, default=None), 'avg': safe_avg(l_vals)},
        'flow':       {'avg': safe_avg(f_vals)},
        'reading_count': len(readings),
    }

    # Alert breakdown
    p_alerts = {'ok': 0, 'warning': 0, 'critical': 0}
    t_alerts = {'ok': 0, 'warning': 0, 'critical': 0}
    l_alerts = {'ok': 0, 'warning': 0, 'critical': 0}
    for r in readings:
        p_alerts[r.pressure_alert or 'ok'] += 1
        t_alerts[r.temp_alert     or 'ok'] += 1
        l_alerts[r.leakage_alert  or 'ok'] += 1

    return jsonify({
        'session': s.to_dict(),
        'chart_data': {
            'timestamps':   timestamps,
            'pressure':     pressures,
            'temperature':  temperatures,
            'flow_rate':    flows,
            'leakage':      leakages,
            'rpm':          rpms,
        },
        'stats':   stats,
        'alerts': {
            'pressure':    p_alerts,
            'temperature': t_alerts,
            'leakage':     l_alerts,
        },
    })


@analysis_bp.route('/pass-fail', methods=['GET'])
@require_token
def pass_fail_chart():
    """Pass vs Fail vs Inconclusive counts for chart."""
    rows = (db.session.query(TestSession.result, func.count(TestSession.id))
            .filter(TestSession.status == 'completed', TestSession.result.isnot(None))
            .group_by(TestSession.result).all())
    counts = {r: c for r, c in rows}
    return jsonify({
        'passed':       counts.get('passed', 0),
        'failed':       counts.get('failed', 0),
        'inconclusive': counts.get('inconclusive', 0),
        'total':        sum(counts.values()),
    })


@analysis_bp.route('/trends', methods=['GET'])
@require_token
def trends():
    """Monthly pass/fail trend for the last 6 months."""
    from datetime import datetime, timedelta
    from sqlalchemy import extract

    months = []
    now = datetime.utcnow()
    for i in range(5, -1, -1):
        month_date = (now.replace(day=1) - timedelta(days=i * 28))
        rows = (db.session.query(TestSession.result, func.count(TestSession.id))
                .filter(
                    TestSession.status == 'completed',
                    extract('year',  TestSession.ended_at) == month_date.year,
                    extract('month', TestSession.ended_at) == month_date.month,
                )
                .group_by(TestSession.result).all())
        counts = {r: c for r, c in rows}
        months.append({
            'month':        month_date.strftime('%b %Y'),
            'passed':       counts.get('passed', 0),
            'failed':       counts.get('failed', 0),
            'inconclusive': counts.get('inconclusive', 0),
        })
    return jsonify({'trends': months})
