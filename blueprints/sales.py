"""
blueprints/sales.py
Sales department: enquiry pipeline management.
Status flow: new → contacted → quotation → won → lost
Won status automatically triggers production order creation.
"""

from flask import Blueprint, jsonify, request
from models import db, Enquiry, ProductionOrder

sales_bp = Blueprint('sales', __name__, url_prefix='/api/sales')


# ============================================================
# ENQUIRY PIPELINE
# ============================================================

@sales_bp.route('/enquiries', methods=['GET'])
def list_enquiries():
    """List enquiries with status filter, search, and pagination."""
    status   = request.args.get('status')
    search   = request.args.get('search', '')
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Enquiry.query

    if status and status in Enquiry.VALID_STATUSES:
        query = query.filter_by(status=status)

    if search:
        query = query.filter(
            Enquiry.name.ilike(f'%{search}%') |
            Enquiry.company.ilike(f'%{search}%') |
            Enquiry.email.ilike(f'%{search}%')
        )

    pagination = query.order_by(Enquiry.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'enquiries': [e.to_dict() for e in pagination.items],
        'total':     pagination.total,
        'pages':     pagination.pages,
        'page':      page
    })


@sales_bp.route('/enquiries/<int:enquiry_id>', methods=['GET'])
def get_enquiry(enquiry_id):
    enquiry = Enquiry.query.get_or_404(enquiry_id)
    return jsonify(enquiry.to_dict())


@sales_bp.route('/enquiries/<int:enquiry_id>/status', methods=['PUT'])
def update_status(enquiry_id):
    """
    Update enquiry status.
    If status transitions to 'won', automatically create a production order.
    """
    enquiry = Enquiry.query.get_or_404(enquiry_id)
    data    = request.get_json()

    new_status = data.get('status')
    if not new_status or new_status not in Enquiry.VALID_STATUSES:
        return jsonify({'error': f'Invalid status. Must be one of: {Enquiry.VALID_STATUSES}'}), 400

    old_status     = enquiry.status
    enquiry.status = new_status
    enquiry.is_read = True   # auto-mark as read when status changes

    if 'estimated_value' in data:
        enquiry.estimated_value = data['estimated_value']

    production_order = None

    # Auto-create production order when deal is won
    if new_status == 'won' and old_status != 'won':
        # Only create if one doesn't already exist for this enquiry
        existing = ProductionOrder.query.filter_by(enquiry_id=enquiry.id).first()
        if not existing:
            production_order = ProductionOrder(
                product_id = enquiry.product_id,
                enquiry_id = enquiry.id,
                quantity   = data.get('quantity', 1),
                status     = 'pending',
                progress   = 0,
                notes      = f'Auto-created from enquiry #{enquiry.id} ({enquiry.company or enquiry.name})'
            )
            db.session.add(production_order)

    try:
        db.session.commit()
        response = {
            'success':  True,
            'enquiry':  enquiry.to_dict(),
        }
        if production_order:
            response['production_order_created'] = True
            response['production_order_id']      = production_order.id
        return jsonify(response)
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@sales_bp.route('/enquiries/<int:enquiry_id>', methods=['PUT'])
def update_enquiry(enquiry_id):
    """Update enquiry details (estimated value, notes, etc.)."""
    enquiry = Enquiry.query.get_or_404(enquiry_id)
    data    = request.get_json()

    if 'estimated_value' in data:
        enquiry.estimated_value = data['estimated_value']
    if 'product_id' in data:
        enquiry.product_id = data['product_id']
    if 'phone' in data:
        enquiry.phone = data['phone']

    try:
        db.session.commit()
        return jsonify({'success': True, 'enquiry': enquiry.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================
# PIPELINE SUMMARY (Kanban / funnel counts)
# ============================================================

@sales_bp.route('/pipeline', methods=['GET'])
def pipeline_summary():
    """Count of enquiries per status for pipeline view."""
    from sqlalchemy import func
    rows = (
        db.session.query(Enquiry.status, func.count(Enquiry.id), func.sum(Enquiry.estimated_value))
        .group_by(Enquiry.status)
        .all()
    )

    summary = {status: {'count': 0, 'value': 0} for status in Enquiry.VALID_STATUSES}
    for status, count, value in rows:
        summary[status] = {
            'count': count,
            'value': float(value) if value else 0
        }

    return jsonify(summary)
