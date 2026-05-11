"""
blueprints/testing_admin.py
Admin-only routes for managing Testing Access Requests and Test Sessions.

Access Requests:
  GET  /api/admin/access-requests          → list all
  GET  /api/admin/access-requests/<id>     → detail
  PUT  /api/admin/access-requests/<id>/approve
  PUT  /api/admin/access-requests/<id>/reject

Test Sessions (read-only view in admin):
  GET  /api/admin/test-sessions            → list + filters
  GET  /api/admin/test-sessions/<id>       → detail with result & readings summary

AI Insights:
  GET  /api/admin/ai-insights              → list
  PUT  /api/admin/ai-insights/<id>/read    → mark read
  DELETE /api/admin/ai-insights/<id>       → dismiss

Activity Log:
  GET  /api/admin/activity                 → recent activity feed
"""
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from models import db
from models_v3 import (
    TestingAccessRequest, TestSession, TestResult,
    AIInsight, ActivityLog, log_activity
)

testing_admin_bp = Blueprint('testing_admin', __name__, url_prefix='/api/admin')


# ═══════════════════════════════════════════════════════════════
# ACCESS REQUESTS
# ═══════════════════════════════════════════════════════════════

@testing_admin_bp.route('/access-requests', methods=['GET'])
def list_access_requests():
    status   = request.args.get('status')          # pending | approved | rejected
    search   = request.args.get('search', '')
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    q = TestingAccessRequest.query
    if status:
        q = q.filter_by(status=status)
    if search:
        q = q.filter(
            TestingAccessRequest.full_name.ilike(f'%{search}%') |
            TestingAccessRequest.email.ilike(f'%{search}%') |
            TestingAccessRequest.company_name.ilike(f'%{search}%')
        )

    pagination = q.order_by(TestingAccessRequest.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Status counts for badges
    counts = {
        'pending':  TestingAccessRequest.query.filter_by(status='pending').count(),
        'approved': TestingAccessRequest.query.filter_by(status='approved').count(),
        'rejected': TestingAccessRequest.query.filter_by(status='rejected').count(),
    }

    return jsonify({
        'requests': [r.to_dict() for r in pagination.items],
        'total':    pagination.total,
        'pages':    pagination.pages,
        'page':     page,
        'counts':   counts,
    })


@testing_admin_bp.route('/access-requests/<int:req_id>', methods=['GET'])
def get_access_request(req_id):
    req = TestingAccessRequest.query.get_or_404(req_id)
    data = req.to_dict()
    # Attach linked sessions if approved
    if req.status == 'approved':
        sessions = TestSession.query.filter_by(access_request_id=req.id).all()
        data['sessions'] = [s.to_dict() for s in sessions]
    return jsonify(data)


@testing_admin_bp.route('/access-requests/<int:req_id>/approve', methods=['PUT'])
def approve_request(req_id):
    req = TestingAccessRequest.query.get_or_404(req_id)
    if req.status == 'approved':
        return jsonify({'error': 'Already approved'}), 409

    data         = request.get_json() or {}
    approved_by  = data.get('approved_by', 'Admin')
    expire_days  = int(data.get('expire_days', 30))

    req.status           = 'approved'
    req.approved_by      = approved_by
    req.actioned_at      = datetime.utcnow()
    req.access_token     = uuid.uuid4().hex        # 32-char hex token
    req.token_expires_at = datetime.utcnow() + timedelta(days=expire_days)

    try:
        log_activity(
            action='approved_access_request',
            entity_type='access_request', entity_id=req.id,
            actor=approved_by,
            description=f"Approved {req.full_name} <{req.email}>, token valid {expire_days}d",
        )
        db.session.commit()
        return jsonify({
            'success':      True,
            'access_token': req.access_token,
            'expires_at':   req.token_expires_at.isoformat(),
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@testing_admin_bp.route('/access-requests/<int:req_id>/reject', methods=['PUT'])
def reject_request(req_id):
    req = TestingAccessRequest.query.get_or_404(req_id)
    if req.status == 'rejected':
        return jsonify({'error': 'Already rejected'}), 409

    data            = request.get_json() or {}
    rejected_by     = data.get('rejected_by', 'Admin')
    rejection_note  = data.get('rejection_note', '')

    req.status          = 'rejected'
    req.approved_by     = rejected_by
    req.rejection_note  = rejection_note
    req.actioned_at     = datetime.utcnow()
    req.access_token    = None

    try:
        log_activity(
            action='rejected_access_request',
            entity_type='access_request', entity_id=req.id,
            actor=rejected_by,
            description=f"Rejected {req.full_name} <{req.email}>. Reason: {rejection_note or 'None'}",
        )
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@testing_admin_bp.route('/access-requests/<int:req_id>/revoke', methods=['PUT'])
def revoke_token(req_id):
    """Revoke an approved token (immediately blocks access)."""
    req = TestingAccessRequest.query.get_or_404(req_id)
    req.access_token     = None
    req.token_expires_at = None
    req.status           = 'rejected'
    req.rejection_note   = 'Token revoked by admin'
    req.actioned_at      = datetime.utcnow()

    try:
        log_activity(
            action='revoked_access_token',
            entity_type='access_request', entity_id=req.id,
            description=f"Revoked token for {req.full_name} <{req.email}>",
        )
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════
# TEST SESSIONS (read-only admin view)
# ═══════════════════════════════════════════════════════════════

@testing_admin_bp.route('/test-sessions', methods=['GET'])
def list_test_sessions():
    status   = request.args.get('status')
    result   = request.args.get('result')
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    q = TestSession.query
    if status:
        q = q.filter_by(status=status)
    if result:
        q = q.filter_by(result=result)

    pagination = q.order_by(TestSession.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Quick counts for dashboard
    from sqlalchemy import func
    counts = dict(
        db.session.query(TestSession.result, func.count(TestSession.id))
        .filter(TestSession.result.isnot(None))
        .group_by(TestSession.result).all()
    )

    return jsonify({
        'sessions': [s.to_dict() for s in pagination.items],
        'total':    pagination.total,
        'pages':    pagination.pages,
        'page':     page,
        'counts':   counts,
    })


@testing_admin_bp.route('/test-sessions/<int:session_id>', methods=['GET'])
def get_test_session(session_id):
    session = TestSession.query.get_or_404(session_id)
    data    = session.to_dict()
    if session.result_record:
        data['result_detail'] = session.result_record.to_dict()
    # Last 10 readings (preview)
    from models_v3 import TestReading
    readings = (TestReading.query
                .filter_by(session_id=session_id)
                .order_by(TestReading.recorded_at.desc())
                .limit(10).all())
    data['latest_readings'] = [r.to_dict() for r in readings]
    return jsonify(data)


# ═══════════════════════════════════════════════════════════════
# AI INSIGHTS
# ═══════════════════════════════════════════════════════════════

@testing_admin_bp.route('/ai-insights', methods=['GET'])
def list_ai_insights():
    unread_only = request.args.get('unread') == '1'
    severity    = request.args.get('severity')

    q = AIInsight.query
    if unread_only:
        q = q.filter_by(is_read=False)
    if severity:
        q = q.filter_by(severity=severity)

    items = q.order_by(AIInsight.generated_at.desc()).limit(50).all()
    unread_count = AIInsight.query.filter_by(is_read=False).count()

    return jsonify({
        'insights':     [i.to_dict() for i in items],
        'unread_count': unread_count,
    })


@testing_admin_bp.route('/ai-insights/<int:insight_id>/read', methods=['PUT'])
def mark_insight_read(insight_id):
    insight = AIInsight.query.get_or_404(insight_id)
    insight.is_read = True
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@testing_admin_bp.route('/ai-insights/read-all', methods=['PUT'])
def mark_all_insights_read():
    AIInsight.query.filter_by(is_read=False).update({'is_read': True})
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@testing_admin_bp.route('/ai-insights/<int:insight_id>', methods=['DELETE'])
def delete_insight(insight_id):
    insight = AIInsight.query.get_or_404(insight_id)
    try:
        db.session.delete(insight)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════
# ACTIVITY LOG
# ═══════════════════════════════════════════════════════════════

@testing_admin_bp.route('/activity', methods=['GET'])
def activity_feed():
    limit       = request.args.get('limit', 30, type=int)
    entity_type = request.args.get('entity_type')

    q = ActivityLog.query
    if entity_type:
        q = q.filter_by(entity_type=entity_type)

    items = q.order_by(ActivityLog.created_at.desc()).limit(min(limit, 100)).all()
    return jsonify({'activity': [a.to_dict() for a in items]})


# ═══════════════════════════════════════════════════════════════
# ADMIN CONTENT MANAGEMENT (Projects, Downloads, Industries)
# ═══════════════════════════════════════════════════════════════

from models_v3 import Project, Download, Industry  # noqa: E402


@testing_admin_bp.route('/projects', methods=['GET'])
def admin_list_projects():
    items = Project.query.order_by(Project.sort_order, Project.created_at.desc()).all()
    return jsonify({'projects': [p.to_dict() for p in items], 'total': len(items)})


@testing_admin_bp.route('/projects', methods=['POST'])
def admin_create_project():
    data = request.get_json() or {}
    if not data.get('title'):
        return jsonify({'error': 'title is required'}), 400
    p = Project(
        title=data['title'], client_name=data.get('client_name'),
        industry=data.get('industry'), problem=data.get('problem'),
        solution=data.get('solution'), result=data.get('result'),
        image_url=data.get('image_url'),
        is_published=bool(data.get('is_published', False)),
        sort_order=int(data.get('sort_order', 0)),
    )
    try:
        db.session.add(p)
        db.session.commit()
        return jsonify({'success': True, 'project': p.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@testing_admin_bp.route('/projects/<int:pid>', methods=['PUT'])
def admin_update_project(pid):
    p    = Project.query.get_or_404(pid)
    data = request.get_json() or {}
    for field in ['title', 'client_name', 'industry', 'problem', 'solution',
                  'result', 'image_url', 'is_published', 'sort_order']:
        if field in data:
            setattr(p, field, data[field])
    try:
        db.session.commit()
        return jsonify({'success': True, 'project': p.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@testing_admin_bp.route('/projects/<int:pid>', methods=['DELETE'])
def admin_delete_project(pid):
    p = Project.query.get_or_404(pid)
    try:
        db.session.delete(p)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@testing_admin_bp.route('/downloads', methods=['GET'])
def admin_list_downloads():
    items = Download.query.order_by(Download.created_at.desc()).all()
    return jsonify({'downloads': [d.to_dict() for d in items], 'total': len(items)})


@testing_admin_bp.route('/downloads', methods=['POST'])
def admin_create_download():
    data = request.get_json() or {}
    if not data.get('title') or not data.get('file_url'):
        return jsonify({'error': 'title and file_url are required'}), 400
    d = Download(
        title=data['title'], description=data.get('description'),
        category=data.get('category', 'brochure'),
        file_url=data['file_url'],
        file_size_kb=data.get('file_size_kb'),
        is_published=bool(data.get('is_published', True)),
    )
    try:
        db.session.add(d)
        db.session.commit()
        return jsonify({'success': True, 'download': d.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@testing_admin_bp.route('/downloads/<int:did>', methods=['DELETE'])
def admin_delete_download(did):
    d = Download.query.get_or_404(did)
    try:
        db.session.delete(d)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@testing_admin_bp.route('/industries', methods=['GET'])
def admin_list_industries():
    items = Industry.query.order_by(Industry.sort_order).all()
    return jsonify({'industries': [i.to_dict() for i in items]})


@testing_admin_bp.route('/industries/<int:iid>', methods=['PUT'])
def admin_update_industry(iid):
    ind  = Industry.query.get_or_404(iid)
    data = request.get_json() or {}
    for field in ['name', 'description', 'icon', 'image_url', 'sort_order', 'is_active']:
        if field in data:
            setattr(ind, field, data[field])
    try:
        db.session.commit()
        return jsonify({'success': True, 'industry': ind.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
