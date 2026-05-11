"""testing_app/blueprints/logs.py — Test logs with filters and pagination."""
from flask import Blueprint, jsonify, request
from testing_app.models import TestSession
from testing_app.auth import require_token

logs_bp = Blueprint('logs', __name__, url_prefix='/api/tests/logs')


@logs_bp.route('', methods=['GET'])
@require_token
def list_logs():
    status   = request.args.get('status')
    result   = request.args.get('result')
    operator = request.args.get('operator')
    date_from= request.args.get('date_from')
    date_to  = request.args.get('date_to')
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)

    q = TestSession.query
    if status:
        q = q.filter_by(status=status)
    if result:
        q = q.filter_by(result=result)
    if operator:
        q = q.filter(TestSession.operator_name.ilike(f'%{operator}%'))
    if date_from:
        from datetime import datetime
        q = q.filter(TestSession.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        from datetime import datetime
        q = q.filter(TestSession.created_at <= datetime.fromisoformat(date_to))

    pg = q.order_by(TestSession.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'logs':  [s.to_dict() for s in pg.items],
        'total': pg.total, 'pages': pg.pages, 'page': page,
    })
