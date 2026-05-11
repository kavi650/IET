"""testing_app/blueprints/results.py — Test result retrieval and export."""
import csv
import io
from flask import Blueprint, jsonify, request, Response
from testing_app.extensions import db
from testing_app.models import TestSession, TestResult, TestReading
from testing_app.auth import require_token

results_bp = Blueprint('results', __name__, url_prefix='/api/tests')


@results_bp.route('/results', methods=['GET'])
@require_token
def list_results():
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    result   = request.args.get('result')    # passed | failed | inconclusive

    q = TestSession.query.filter(TestSession.status == 'completed')
    if result:
        q = q.filter_by(result=result)

    pg = q.order_by(TestSession.ended_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    items = []
    for s in pg.items:
        d = s.to_dict()
        if s.result_record:
            d['summary'] = s.result_record.to_dict()
        items.append(d)

    return jsonify({'results': items, 'total': pg.total, 'pages': pg.pages, 'page': page})


@results_bp.route('/results/<int:session_id>', methods=['GET'])
@require_token
def get_result(session_id):
    s = TestSession.query.get_or_404(session_id)
    data = s.to_dict()
    if s.result_record:
        data['result_detail'] = s.result_record.to_dict()
    return jsonify(data)


# ── CSV Export ────────────────────────────────────────────────

@results_bp.route('/sessions/<int:session_id>/export/csv', methods=['GET'])
@require_token
def export_csv(session_id):
    s = TestSession.query.get_or_404(session_id)
    readings = (TestReading.query
                .filter_by(session_id=session_id)
                .order_by(TestReading.recorded_at.asc()).all())

    output = io.StringIO()
    writer = csv.writer(output)

    # Header block
    writer.writerow(['Testiny Equipments — Test Report'])
    writer.writerow(['Session Code', s.session_code])
    writer.writerow(['Operator',     s.operator_name])
    writer.writerow(['Valve ID',     s.valve_id or ''])
    writer.writerow(['Valve Type',   s.valve_type or ''])
    writer.writerow(['Test Type',    s.test_type])
    writer.writerow(['Medium',       s.medium])
    writer.writerow(['Result',       (s.result or '').upper()])
    writer.writerow(['Duration (s)', s.duration_seconds or ''])
    writer.writerow([])

    # Readings table
    writer.writerow(['Timestamp', 'Pressure (bar)', 'Temperature (°C)',
                     'Flow Rate (LPM)', 'Leakage (mL/min)', 'RPM',
                     'Pressure Alert', 'Temp Alert', 'Leakage Alert'])
    for r in readings:
        writer.writerow([
            r.recorded_at.strftime('%Y-%m-%d %H:%M:%S'),
            r.pressure_bar or '', r.temperature_c or '',
            r.flow_rate_lpm or '', r.leakage_ml_min or '', r.rpm or '',
            r.pressure_alert, r.temp_alert, r.leakage_alert,
        ])

    filename = f"Testiny_{s.session_code}_{s.valve_id or 'test'}.csv"
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


# ── Sign result ───────────────────────────────────────────────

@results_bp.route('/results/<int:session_id>/sign', methods=['PUT'])
@require_token
def sign_result(session_id):
    from datetime import datetime
    s = TestSession.query.get_or_404(session_id)
    if not s.result_record:
        return jsonify({'error': 'No result record found for this session'}), 404

    data = request.get_json() or {}
    engineer = data.get('engineer_name', '').strip()
    if not engineer:
        return jsonify({'error': 'engineer_name is required'}), 400

    s.result_record.engineer_signed_by = engineer
    s.result_record.signed_at          = datetime.utcnow()
    try:
        db.session.commit()
        return jsonify({'success': True, 'signed_by': engineer})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
